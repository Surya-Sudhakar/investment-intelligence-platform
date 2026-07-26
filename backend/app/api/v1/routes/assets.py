from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.assets.dependencies import get_asset_intelligence_service
from app.modules.assets.schemas import AssetIntelligenceResponse
from app.modules.assets.service import AssetIntelligenceService

router = APIRouter(prefix="/assets", tags=["assets"])
type Service = Annotated[AssetIntelligenceService, Depends(get_asset_intelligence_service)]


@router.get("/{symbol}/intelligence", response_model=AssetIntelligenceResponse)
async def asset_intelligence(symbol: str, service: Service) -> AssetIntelligenceResponse:
    return await service.get_intelligence(symbol)
