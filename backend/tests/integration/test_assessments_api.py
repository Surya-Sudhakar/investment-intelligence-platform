from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import app
from app.modules.assessments.dependencies import get_assessment_service
from app.modules.assessments.schemas import AssessmentHealth
from app.modules.assessments.scoring import build_assessment
from tests.unit.test_assessment_scoring import snapshot

NOW = datetime(2026, 7, 25, 12, tzinfo=UTC)


class FakeAssessmentService:
    async def health(self) -> AssessmentHealth:
        return AssessmentHealth(
            status="healthy",
            scoring_version="technical-v1",
            intelligence_ready=True,
            checked_at=NOW,
            message="ready",
        )

    async def assess(self, symbol: str):
        return build_assessment(snapshot().model_copy(update={"symbol": symbol.upper()}), NOW)


def test_assessment_endpoint_is_daily_only(client: TestClient) -> None:
    app.dependency_overrides[get_assessment_service] = lambda: FakeAssessmentService()

    response = client.get("/api/v1/assessments/aapl?interval=1day")
    assert response.status_code == 200
    assert response.json()["symbol"] == "AAPL"
    assert response.json()["scoring_version"] == "technical-v1"

    unsupported = client.get("/api/v1/assessments/aapl?interval=1h")
    assert unsupported.status_code == 422
    assert unsupported.json()["error"]["code"] == "UNSUPPORTED_INTERVAL"

    health = client.get("/api/v1/assessments/health")
    assert health.status_code == 200
    assert health.json()["intelligence_ready"] is True
