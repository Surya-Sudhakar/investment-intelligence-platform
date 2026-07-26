from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.exceptions import ProviderRateLimitError, ProviderUnavailableError
from app.main import app
from app.modules.assets.dependencies import get_asset_intelligence_service
from app.modules.assets.schemas import (
    AssetAvailability,
    AssetIntelligenceResponse,
    AssetType,
    StockProfile,
)


class FakeAssetService:
    async def get_intelligence(self, symbol: str) -> AssetIntelligenceResponse:
        return AssetIntelligenceResponse(
            symbol=symbol.upper(),
            display_name="Apple Inc.",
            asset_type=AssetType.STOCK,
            exchange="NASDAQ",
            currency="USD",
            provider="test",
            generated_at=datetime(2026, 7, 26, tzinfo=UTC),
            profile=StockProfile(company_name="Apple Inc."),
            warnings=[],
            availability=AssetAvailability(profile=True),
        )


class FailingAssetService:
    def __init__(self, error: Exception) -> None:
        self.error = error

    async def get_intelligence(self, symbol: str) -> AssetIntelligenceResponse:
        del symbol
        raise self.error


def test_asset_intelligence_endpoint(client: TestClient) -> None:
    app.dependency_overrides[get_asset_intelligence_service] = lambda: FakeAssetService()

    response = client.get("/api/v1/assets/aapl/intelligence")

    assert response.status_code == 200
    assert response.json()["asset_type"] == "STOCK"
    assert response.json()["profile"]["company_name"] == "Apple Inc."


def test_asset_provider_errors_use_standard_envelope(client: TestClient) -> None:
    app.dependency_overrides[get_asset_intelligence_service] = lambda: FailingAssetService(
        ProviderRateLimitError()
    )
    limited = client.get("/api/v1/assets/AAPL/intelligence")
    assert limited.status_code == 429
    assert limited.json()["error"]["code"] == "MARKET_PROVIDER_RATE_LIMITED"

    app.dependency_overrides[get_asset_intelligence_service] = lambda: FailingAssetService(
        ProviderUnavailableError()
    )
    unavailable = client.get("/api/v1/assets/AAPL/intelligence")
    assert unavailable.status_code == 503
    assert unavailable.json()["error"]["code"] == "MARKET_PROVIDER_UNAVAILABLE"
