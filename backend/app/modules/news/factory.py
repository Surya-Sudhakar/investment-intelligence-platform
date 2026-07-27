from app.core.config import Settings
from app.modules.market_data.http_client import MarketDataHttpClient
from app.modules.news.alpha_vantage import AlphaVantageNewsProvider
from app.modules.news.provider import NewsProvider


def build_news_provider(settings: Settings, client: MarketDataHttpClient) -> NewsProvider:
    return AlphaVantageNewsProvider(settings.news_api_key, settings.news_base_url, client)
