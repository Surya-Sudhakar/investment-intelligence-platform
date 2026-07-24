from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.exceptions import DatabaseUnavailableError
from app.db.session import check_database, get_db
from app.schemas.common import HealthResponse, ReadyResponse

router = APIRouter(tags=["status"])


@router.get("/health", response_model=HealthResponse)
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(UTC),
    )


@router.get("/ready", response_model=ReadyResponse)
def ready(
    session: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ReadyResponse:
    try:
        check_database(session)
    except SQLAlchemyError as exc:
        raise DatabaseUnavailableError() from exc
    return ReadyResponse(
        status="ready",
        service=settings.app_name,
        version=settings.app_version,
        timestamp=datetime.now(UTC),
        application="initialized",
        database="connected",
    )
