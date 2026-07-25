from typing import Annotated

from fastapi import APIRouter, Depends

from app.modules.intelligence.dependencies import get_intelligence_service
from app.modules.intelligence.schemas import IntelligenceHealth, IntelligenceSnapshot
from app.modules.intelligence.service import IntelligenceService

router = APIRouter(prefix="/intelligence", tags=["intelligence"])
type Service = Annotated[IntelligenceService, Depends(get_intelligence_service)]


@router.get("/health", response_model=IntelligenceHealth)
async def intelligence_health(service: Service) -> IntelligenceHealth:
    return await service.health()


@router.get("/{symbol}", response_model=IntelligenceSnapshot)
async def intelligence_snapshot(symbol: str, service: Service) -> IntelligenceSnapshot:
    return await service.snapshot(symbol)
