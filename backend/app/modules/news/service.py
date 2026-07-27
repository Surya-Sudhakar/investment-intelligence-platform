from datetime import UTC, datetime

from app.modules.assets.service import AssetIntelligenceService
from app.modules.market_data.cache import TTLCache
from app.modules.news.grouping import group_articles
from app.modules.news.provider import NewsProvider
from app.modules.news.schemas import (
    AssetNewsAggregate,
    AssetNewsIntelligence,
    NewsArticle,
    NewsFreshness,
    NewsFreshnessMetadata,
    NewsSentiment,
)
from app.modules.news.sentiment import classify_category, classify_sentiment
from app.modules.news.summarization import asset_summary, concise_summary


class NewsIntelligenceService:
    def __init__(
        self,
        provider: NewsProvider,
        assets: AssetIntelligenceService,
        cache: TTLCache,
        cache_ttl: int,
        empty_ttl: int,
        fresh_hours: int,
        recent_hours: int,
    ) -> None:
        self.provider, self.assets, self.cache = provider, assets, cache
        self.cache_ttl, self.empty_ttl = cache_ttl, empty_ttl
        self.fresh_hours, self.recent_hours = fresh_hours, recent_hours

    def _freshness(self, published: datetime | None, now: datetime) -> NewsFreshnessMetadata:
        if not published:
            return NewsFreshnessMetadata(
                state=NewsFreshness.UNKNOWN, age_seconds=None, evaluated_at=now
            )
        age = max(0, int((now - published).total_seconds()))
        state = (
            NewsFreshness.FRESH
            if age <= self.fresh_hours * 3600
            else NewsFreshness.RECENT
            if age <= self.recent_hours * 3600
            else NewsFreshness.STALE
        )
        return NewsFreshnessMetadata(state=state, age_seconds=age, evaluated_at=now)

    async def get_news(self, symbol: str, limit: int) -> AssetNewsIntelligence:
        resolution = await self.assets.resolve_asset(symbol)
        key = f"news:{self.provider.name}:{resolution.asset_type}:{resolution.symbol}:{limit}"
        cached = await self.cache.get(key)
        if isinstance(cached, AssetNewsIntelligence):
            return cached.model_copy(deep=True)
        now = datetime.now(UTC)
        raw = await self.provider.fetch_news(resolution, limit)
        unique, seen_ids, seen_urls = [], set(), set()
        for item in raw:
            normalized_url = str(item.url).casefold()
            if item.id in seen_ids or normalized_url in seen_urls:
                continue
            seen_ids.add(item.id)
            seen_urls.add(normalized_url)
            relevance = item.relevance_score or 50
            sentiment, confidence, factors = classify_sentiment(item)
            text = f"{item.title} {item.summary}"
            article = NewsArticle(
                **item.model_dump(exclude={"relevance_score"}),
                asset_symbol=resolution.symbol,
                asset_type=resolution.asset_type,
                category=classify_category(text, resolution.asset_type),
                relevance_score=relevance,
                sentiment=sentiment,
                confidence=confidence,
                freshness=self._freshness(item.published_at, now),
                sentiment_factors=factors,
            )
            article.summary = concise_summary(article)
            unique.append(article)
        groups = group_articles(unique)
        counts = {state: sum(a.sentiment is state for a in unique) for state in NewsSentiment}
        scored = [a for a in unique if a.sentiment is not NewsSentiment.UNKNOWN]
        weighted = sum(
            (
                1
                if a.sentiment is NewsSentiment.POSITIVE
                else -1
                if a.sentiment is NewsSentiment.NEGATIVE
                else 0
            )
            * a.confidence
            * a.relevance_score
            for a in scored
        )
        overall = (
            NewsSentiment.UNKNOWN
            if not scored
            else NewsSentiment.POSITIVE
            if weighted > 0
            else NewsSentiment.NEGATIVE
            if weighted < 0
            else NewsSentiment.NEUTRAL
        )
        confidence = 0 if not scored else round(sum(a.confidence for a in scored) / len(scored))
        aggregate = AssetNewsAggregate(
            positive_count=counts[NewsSentiment.POSITIVE],
            neutral_count=counts[NewsSentiment.NEUTRAL],
            negative_count=counts[NewsSentiment.NEGATIVE],
            unknown_count=counts[NewsSentiment.UNKNOWN],
            overall_sentiment=overall,
            confidence=confidence,
            explanation=(
                "No sufficiently relevant articles were available."
                if not scored
                else f"The result reflects {len(scored)} classified, deduplicated articles."
            ),
        )
        latest = max((a.published_at for a in unique), default=None)
        warnings = [] if unique else ["No recent news was returned by the provider."]
        result = AssetNewsIntelligence(
            symbol=resolution.symbol,
            asset_type=resolution.asset_type,
            provider=self.provider.name,
            articles=unique,
            groups=groups,
            aggregate=aggregate,
            summary=asset_summary(unique, resolution.symbol),
            freshness=self._freshness(latest, now),
            generated_at=now,
            warnings=warnings,
        )
        await self.cache.set(key, result, self.cache_ttl if unique else self.empty_ttl)
        return result
