from app.core.config import Settings
from app.modules.market_data.alpha_vantage import AlphaVantageProvider
from app.modules.market_data.http_client import MarketDataHttpClient
from app.modules.market_data.provider import MarketDataProvider, ProviderRegistry
from app.modules.market_data.twelve_data import TwelveDataProvider


def build_provider(settings: Settings, client: MarketDataHttpClient) -> MarketDataProvider:
    registry = ProviderRegistry()
    registry.register(
        AlphaVantageProvider(
            api_key=settings.market_data_api_key,
            base_url=settings.market_data_base_url,
            client=client,
        )
    )
    registry.register(
        TwelveDataProvider(
            api_key=settings.market_data_api_key,
            base_url=settings.market_data_base_url,
            client=client,
        )
    )
    return registry.get(settings.market_data_provider)
