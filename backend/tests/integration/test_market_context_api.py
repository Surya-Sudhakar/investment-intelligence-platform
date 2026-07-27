from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.core.exceptions import UnsupportedAssetError
from app.main import app
from app.modules.market_context.dependencies import get_market_context_service
from app.modules.market_context.schemas import MarketContextResponse


def item(status: str, reason: str, value: object | None = None) -> dict[str, object]:
    return {"status": status, "value": value, "reason": reason}


def context_response() -> MarketContextResponse:
    unavailable = item("unavailable", "Provider data is unavailable.")
    not_applicable = item("not_applicable", "Not applicable to stocks.")
    now = datetime.now(UTC)
    return MarketContextResponse.model_validate(
        {
            "symbol": "AAPL",
            "display_name": "Apple Inc.",
            "asset_type": "STOCK",
            "provider": "test",
            "methodology_version": "market-context-v1",
            "horizon": {"interval": "1day", "lookback_sessions": 20},
            "overall_context": item("available", "Calculated.", "POSITIVE"),
            "confidence": 75,
            "partial_data_status": "partial",
            "market": {
                "primary_exchange": item("available", "Provided.", "NASDAQ"),
                "primary_market_index": unavailable,
                "reference": unavailable,
                "performance": unavailable,
            },
            "sector": {
                "name": item("available", "Provided.", "Technology"),
                "reference": unavailable,
                "performance": unavailable,
                "trend": unavailable,
            },
            "industry": {
                "name": item("available", "Provided.", "Software"),
                "reference": unavailable,
                "performance": unavailable,
                "trend": unavailable,
            },
            "commodity": {
                "precious_metals_trend": not_applicable,
                "silver_comparison": not_applicable,
                "commodity_index_trend": not_applicable,
                "safe_haven_demand_trend": not_applicable,
                "commodity_market_alignment": not_applicable,
            },
            "etf": {
                "etf_category": not_applicable,
                "fund_category": not_applicable,
                "benchmark_index": not_applicable,
                "regional_exposure": not_applicable,
                "sector_concentration": not_applicable,
                "relative_performance": not_applicable,
            },
            "relative_strength": {
                "versus_market": unavailable,
                "versus_sector": unavailable,
                "versus_industry": unavailable,
            },
            "supporting_observations": [],
            "warnings": [],
            "freshness": {
                "status": "unavailable",
                "reason": "No observations.",
            },
            "availability": {
                "asset_performance": "unavailable",
                "market": "unavailable",
                "sector": "unavailable",
                "industry": "unavailable",
                "relative_strength": "unavailable",
                "commodity": "not_applicable",
                "etf": "not_applicable",
            },
            "source_timestamp": unavailable,
            "generated_at": now,
        }
    )


class FakeContextService:
    async def get_context(self, symbol: str) -> MarketContextResponse:
        del symbol
        return context_response()


class UnknownContextService:
    async def get_context(self, symbol: str) -> MarketContextResponse:
        raise UnsupportedAssetError(symbol)


def test_market_context_endpoint_uses_normalized_schema(client: TestClient) -> None:
    app.dependency_overrides[get_market_context_service] = lambda: FakeContextService()

    response = client.get("/api/v1/assets/aapl/market-context")

    assert response.status_code == 200
    payload = response.json()
    assert payload["overall_context"]["value"] == "POSITIVE"
    assert payload["market"]["primary_market_index"]["status"] == "unavailable"
    assert payload["commodity"]["precious_metals_trend"]["status"] == "not_applicable"


def test_unknown_market_context_asset_uses_standard_error(client: TestClient) -> None:
    app.dependency_overrides[get_market_context_service] = lambda: UnknownContextService()

    response = client.get("/api/v1/assets/UNKNOWN/market-context")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "UNSUPPORTED_ASSET"
