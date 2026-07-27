from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import app
from app.modules.assets.schemas import AssetType
from app.modules.news.dependencies import get_news_service
from app.modules.news.schemas import (
    AssetNewsAggregate,
    AssetNewsIntelligence,
    NewsFreshnessMetadata,
)


class Service:
    async def get_news(self, symbol: str, limit: int) -> AssetNewsIntelligence:
        return AssetNewsIntelligence(
            symbol=symbol.upper(),
            asset_type=AssetType.STOCK,
            provider="test",
            articles=[],
            groups=[],
            aggregate=AssetNewsAggregate(
                positive_count=0,
                neutral_count=0,
                negative_count=0,
                unknown_count=0,
                overall_sentiment="UNKNOWN",
                confidence=0,
                explanation=f"No articles in limit {limit}.",
            ),
            summary="Insufficient recent information is available to summarize.",
            freshness=NewsFreshnessMetadata(
                state="UNKNOWN", age_seconds=None, evaluated_at=datetime.now(UTC)
            ),
            generated_at=datetime.now(UTC),
        )


def test_news_endpoint_and_limit_validation(client: TestClient) -> None:
    app.dependency_overrides[get_news_service] = lambda: Service()
    response = client.get("/api/v1/assets/aapl/news?limit=10")
    assert response.status_code == 200
    assert response.json()["symbol"] == "AAPL"
    invalid = client.get("/api/v1/assets/aapl/news?limit=0")
    assert invalid.status_code == 422
