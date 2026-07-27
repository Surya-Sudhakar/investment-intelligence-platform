from datetime import UTC, datetime
from typing import Any

from app.core.exceptions import (
    NewsProviderConfigurationError,
    ProviderAuthenticationError,
    ProviderInvalidResponseError,
    ProviderRateLimitError,
)
from app.modules.assets.schemas import AssetResolution, AssetType
from app.modules.market_data.http_client import MarketDataHttpClient
from app.modules.news.schemas import ProviderNewsArticle


class AlphaVantageNewsProvider:
    name = "alpha_vantage"

    def __init__(self, api_key: str | None, base_url: str, client: MarketDataHttpClient) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.client = client

    async def fetch_news(
        self, resolution: AssetResolution, limit: int
    ) -> list[ProviderNewsArticle]:
        if not self.api_key:
            raise NewsProviderConfigurationError()
        params = {
            "function": "NEWS_SENTIMENT",
            "sort": "LATEST",
            "limit": str(limit),
            "apikey": self.api_key,
        }
        if resolution.asset_type is AssetType.GOLD:
            params["topics"] = "economy_monetary,economy_macro,financial_markets,finance"
        else:
            params["tickers"] = resolution.provider_symbol
        payload = await self.client.get_json(self.base_url, params)
        information = str(payload.get("Information", ""))
        if "api key" in information.casefold():
            raise ProviderAuthenticationError()
        if "rate limit" in information.casefold() or "Note" in payload:
            raise ProviderRateLimitError()
        feed = payload.get("feed")
        if feed is None:
            return []
        if not isinstance(feed, list):
            raise ProviderInvalidResponseError()
        articles = []
        for item in feed:
            if not isinstance(item, dict):
                continue
            article = self._parse(item, resolution)
            if article:
                articles.append(article)
        return articles

    def _parse(
        self, item: dict[str, Any], resolution: AssetResolution
    ) -> ProviderNewsArticle | None:
        title, url = str(item.get("title", "")).strip(), str(item.get("url", "")).strip()
        if not title or not url.startswith(("https://", "http://")):
            return None
        text = f"{title} {item.get('summary', '')}".casefold()
        if resolution.asset_type is AssetType.GOLD and not any(
            word in text for word in ("gold", "bullion", "xau", "safe-haven", "central bank")
        ):
            return None
        raw_time = str(item.get("time_published", ""))
        try:
            published = datetime.strptime(raw_time[:15], "%Y%m%dT%H%M%S").replace(tzinfo=UTC)
        except ValueError:
            return None
        relevance = None
        scores = item.get("ticker_sentiment")
        if isinstance(scores, list):
            for score in scores:
                if isinstance(score, dict) and str(score.get("ticker", "")).upper() in {
                    resolution.provider_symbol,
                    resolution.symbol,
                }:
                    try:
                        relevance = round(float(score["relevance_score"]) * 100)
                    except (KeyError, TypeError, ValueError):
                        pass
        return ProviderNewsArticle(
            id=str(item.get("id") or url),
            title=title,
            summary=str(item.get("summary") or ""),
            source=str(item.get("source") or "Unknown"),
            published_at=published,
            url=url,
            language=str(item.get("language") or "") or None,
            provider=self.name,
            relevance_score=relevance,
        )
