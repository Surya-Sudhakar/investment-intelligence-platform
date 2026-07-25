from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.config import Settings, get_settings
from app.core.exceptions import UnsupportedIntervalError
from app.modules.market_data.dependencies import get_market_data_service
from app.modules.market_data.schemas import (
    CandleResponse,
    Interval,
    ProviderCapabilities,
    ProviderHealth,
    Quote,
    SymbolDetails,
    SymbolSearchResult,
)
from app.modules.market_data.service import MarketDataService

router = APIRouter(tags=["market-data"])
type Service = Annotated[MarketDataService, Depends(get_market_data_service)]


@router.get("/market-data/provider", response_model=ProviderCapabilities)
def provider_capabilities(service: Service) -> ProviderCapabilities:
    return service.capabilities()


@router.get("/market-data/health", response_model=ProviderHealth)
async def provider_health(service: Service) -> ProviderHealth:
    return await service.health()


@router.get("/symbols/search", response_model=list[SymbolSearchResult])
async def search_symbols(
    service: Service,
    q: Annotated[str, Query(min_length=2, max_length=100)],
    limit: Annotated[int, Query(ge=1, le=25)] = 10,
) -> list[SymbolSearchResult]:
    if len(q.strip()) < 2:
        raise HTTPException(status_code=422, detail="q must contain at least two characters")
    return await service.search_symbols(q, limit)


@router.get("/symbols/{symbol}", response_model=SymbolDetails)
async def symbol_details(symbol: str, service: Service) -> SymbolDetails:
    return await service.symbol_details(symbol)


@router.get("/market-data/{symbol}/candles", response_model=CandleResponse)
async def candles(
    symbol: str,
    service: Service,
    settings: Annotated[Settings, Depends(get_settings)],
    interval: str,
    limit: Annotated[int | None, Query(ge=1)] = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> CandleResponse:
    try:
        canonical_interval = Interval(interval)
    except ValueError as exc:
        raise UnsupportedIntervalError(interval) from exc
    requested_limit = limit or settings.market_data_default_candle_limit
    if requested_limit > settings.market_data_max_candle_limit:
        raise HTTPException(
            status_code=422,
            detail=f"limit must be at most {settings.market_data_max_candle_limit}",
        )
    if (start and start.tzinfo is None) or (end and end.tzinfo is None):
        raise HTTPException(status_code=422, detail="start and end must include a timezone")
    start = start.astimezone(UTC) if start else None
    end = end.astimezone(UTC) if end else None
    if start and end and start >= end:
        raise HTTPException(status_code=422, detail="start must be earlier than end")
    return await service.candles(symbol, canonical_interval, start, end, requested_limit)


@router.get("/market-data/{symbol}/quote", response_model=Quote)
async def quote(symbol: str, service: Service) -> Quote:
    return await service.quote(symbol)
