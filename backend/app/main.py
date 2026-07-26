import logging
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import RequestResponseEndpoint

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import configure_logging
from app.modules.assessments.service import AssessmentService
from app.modules.assets.provider import AssetDataProvider
from app.modules.assets.service import AssetIntelligenceService
from app.modules.intelligence.polling import QuotePollingEngine
from app.modules.intelligence.service import IntelligenceService
from app.modules.market_data.cache import TTLCache
from app.modules.market_data.factory import build_provider
from app.modules.market_data.http_client import MarketDataHttpClient
from app.modules.market_data.service import MarketDataService

logger = logging.getLogger(__name__)


def error_response(
    request: Request, code: str, message: str, status_code: int, details: object | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": str(request.state.request_id),
            }
        },
    )


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.app_name, settings.app_env, settings.log_level, settings.log_json)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        market_client = MarketDataHttpClient(
            timeout_seconds=settings.market_data_timeout_seconds,
            max_retries=settings.market_data_max_retries,
        )
        provider = build_provider(settings, market_client)
        market_data_service = MarketDataService(
            provider,
            TTLCache(enabled=settings.market_data_cache_enabled),
            settings,
        )
        polling = QuotePollingEngine(
            market_data_service.quote, settings.intelligence_poll_interval_seconds
        )
        app.state.market_data_service = market_data_service
        intelligence_service = IntelligenceService(market_data_service, polling, settings)
        app.state.intelligence_service = intelligence_service
        app.state.assessment_service = AssessmentService(intelligence_service)
        app.state.asset_intelligence_service = AssetIntelligenceService(
            cast(AssetDataProvider, provider),
            market_data_service,
            intelligence_service,
            market_data_service.cache,
            settings,
        )
        logger.info("Application initialized")
        yield
        await polling.stop_all()
        await market_client.close()
        logger.info("Application stopped")

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=False,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=False,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    @application.middleware("http")
    async def request_context(request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "route": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        return response

    @application.exception_handler(AppException)
    async def app_exception(request: Request, exc: AppException) -> JSONResponse:
        logger.exception("Application error", extra={"error_type": type(exc).__name__})
        return error_response(request, exc.code, exc.message, exc.status_code, exc.details)

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"field": ".".join(map(str, error["loc"])), "message": error["msg"]}
            for error in exc.errors()
        ]
        return error_response(request, "VALIDATION_ERROR", "The request is invalid.", 422, details)

    @application.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            return error_response(
                request, "NOT_FOUND", "The requested resource was not found.", 404
            )
        return error_response(
            request, "HTTP_ERROR", "The request could not be completed.", exc.status_code
        )

    @application.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unexpected error", extra={"error_type": type(exc).__name__})
        return error_response(request, "INTERNAL_ERROR", "An unexpected error occurred.", 500)

    @application.get("/", tags=["root"])
    def root() -> dict[str, str]:
        return {"status": "running", "service": settings.app_name, "version": settings.app_version}

    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
