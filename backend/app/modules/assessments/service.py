from datetime import UTC, datetime

from app.modules.assessments.config import TECHNICAL_V1
from app.modules.assessments.schemas import AssessmentHealth, TechnicalAssessment
from app.modules.assessments.scoring import build_assessment
from app.modules.intelligence.service import IntelligenceService


class AssessmentService:
    def __init__(self, intelligence: IntelligenceService) -> None:
        self.intelligence = intelligence

    async def assess(self, symbol: str) -> TechnicalAssessment:
        snapshot = await self.intelligence.snapshot(symbol)
        return build_assessment(snapshot)

    async def health(self) -> AssessmentHealth:
        checked_at = datetime.now(UTC)
        intelligence_health = await self.intelligence.health()
        ready = intelligence_health.status == "healthy"
        return AssessmentHealth(
            status="healthy" if ready else "unavailable",
            scoring_version=TECHNICAL_V1.version,
            intelligence_ready=ready,
            checked_at=checked_at,
            message=(
                "Technical assessment service is ready."
                if ready
                else "Technical assessment inputs are unavailable."
            ),
        )
