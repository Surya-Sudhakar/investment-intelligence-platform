from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import UnsupportedIntervalError
from app.modules.assessments.dependencies import get_assessment_service
from app.modules.assessments.schemas import AssessmentHealth, TechnicalAssessment
from app.modules.assessments.service import AssessmentService
from app.modules.market_data.schemas import Interval

router = APIRouter(prefix="/assessments", tags=["assessments"])
type Service = Annotated[AssessmentService, Depends(get_assessment_service)]


@router.get("/health", response_model=AssessmentHealth)
async def assessment_health(service: Service) -> AssessmentHealth:
    return await service.health()


@router.get("/{symbol}", response_model=TechnicalAssessment)
async def technical_assessment(
    symbol: str,
    service: Service,
    interval: str = Query(default=Interval.ONE_DAY.value),
) -> TechnicalAssessment:
    if interval != Interval.ONE_DAY.value:
        raise UnsupportedIntervalError(interval)
    return await service.assess(symbol)
