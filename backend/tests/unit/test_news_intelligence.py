import asyncio
from datetime import UTC, datetime, timedelta

from app.modules.assets.schemas import AssetResolution, AssetType
from app.modules.market_data.cache import TTLCache
from app.modules.news.grouping import group_articles
from app.modules.news.schemas import NewsArticle, NewsFreshnessMetadata, ProviderNewsArticle
from app.modules.news.sentiment import classify_sentiment
from app.modules.news.service import NewsIntelligenceService

NOW = datetime.now(UTC)


def raw(title: str, *, id: str = "1") -> ProviderNewsArticle:
    return ProviderNewsArticle(
        id=id,
        title=title,
        summary="The company raises guidance after record revenue.",
        source="Example",
        published_at=NOW - timedelta(hours=1),
        url=f"https://example.com/{id}",
        provider="test",
        relevance_score=90,
    )


def test_sentiment_is_deterministic() -> None:
    positive, confidence, factors = classify_sentiment(raw("Company raises guidance"))
    negative, _, _ = classify_sentiment(
        raw("Company misses expectations and lowers guidance", id="2")
    )
    assert positive.value == "POSITIVE"
    assert negative.value == "NEGATIVE"
    assert confidence > 50
    assert factors


class Assets:
    async def resolve_asset(self, symbol: str) -> AssetResolution:
        return AssetResolution(
            symbol=symbol.upper(),
            provider_symbol=symbol.upper(),
            asset_type=AssetType.STOCK,
        )


class Provider:
    name = "test"

    def __init__(self, articles: list[ProviderNewsArticle]) -> None:
        self.articles, self.calls = articles, 0

    async def fetch_news(self, resolution: AssetResolution, limit: int):
        self.calls += 1
        return self.articles[:limit]


def test_service_deduplicates_caches_and_aggregates() -> None:
    provider = Provider([raw("Company raises guidance"), raw("Company raises guidance")])
    service = NewsIntelligenceService(
        provider,
        Assets(),
        TTLCache(),
        900,
        300,
        6,
        24,  # type: ignore[arg-type]
    )
    first = asyncio.run(service.get_news("aapl", 20))
    second = asyncio.run(service.get_news("AAPL", 20))
    assert len(first.articles) == 1
    assert first.aggregate.overall_sentiment.value == "POSITIVE"
    assert provider.calls == 1
    assert second.summary == first.summary


def test_empty_news_is_safe() -> None:
    service = NewsIntelligenceService(
        Provider([]),
        Assets(),
        TTLCache(),
        900,
        300,
        6,
        24,  # type: ignore[arg-type]
    )
    result = asyncio.run(service.get_news("AAPL", 20))
    assert result.aggregate.overall_sentiment.value == "UNKNOWN"
    assert "Insufficient" in result.summary
    assert result.warnings


def test_low_relevance_articles_are_excluded_from_output() -> None:
    article = raw("Unrelated fund profile")
    article.relevance_score = 10
    service = NewsIntelligenceService(
        Provider([article]),
        Assets(),
        TTLCache(),
        900,
        300,
        6,
        24,  # type: ignore[arg-type]
    )
    result = asyncio.run(service.get_news("AAPL", 20))
    assert result.articles == []
    assert result.aggregate.overall_sentiment.value == "UNKNOWN"


def test_grouping_combines_duplicate_titles() -> None:
    base = raw("Apple announces product", id="a")
    sentiment, confidence, factors = classify_sentiment(base)
    article = NewsArticle(
        **base.model_dump(exclude={"relevance_score"}),
        asset_symbol="AAPL",
        asset_type=AssetType.STOCK,
        category="PRODUCT",
        relevance_score=90,
        sentiment=sentiment,
        confidence=confidence,
        freshness=NewsFreshnessMetadata(state="FRESH", age_seconds=0, evaluated_at=NOW),
        sentiment_factors=factors,
    )
    groups = group_articles([article, article.model_copy(update={"id": "b"})])
    assert groups[0].article_count == 2
