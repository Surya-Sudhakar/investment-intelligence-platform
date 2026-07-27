from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.modules.news.dependencies import get_news_service
from app.modules.news.schemas import AssetNewsIntelligence
from app.modules.news.service import NewsIntelligenceService

router = APIRouter(prefix="/assets", tags=["news"])
Service = Annotated[NewsIntelligenceService, Depends(get_news_service)]


@router.get("/{symbol}/news", response_model=AssetNewsIntelligence)
async def asset_news(
    symbol: str, service: Service, limit: Annotated[int, Query(ge=1, le=50)] = 20
) -> AssetNewsIntelligence:
    return await service.get_news(symbol, limit)
