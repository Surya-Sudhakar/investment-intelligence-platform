from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.market_context.dependencies import get_market_context_service
from app.modules.market_context.schemas import MarketContextResponse
from app.modules.market_context.service import MarketContextService

router = APIRouter(prefix="/assets", tags=["market-context"])
type Service = Annotated[MarketContextService, Depends(get_market_context_service)]


@router.get("/{symbol}/market-context", response_model=MarketContextResponse)
async def market_context(symbol: str, service: Service) -> MarketContextResponse:
    return await service.get_context(symbol)
