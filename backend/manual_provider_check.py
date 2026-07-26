"""Optional manual verification against the configured genuine provider."""

import asyncio

from app.core.config import get_settings
from app.modules.market_data.factory import build_provider
from app.modules.market_data.http_client import MarketDataHttpClient
from app.modules.market_data.schemas import Interval


async def main() -> None:
    settings = get_settings()
    client = MarketDataHttpClient(
        timeout_seconds=settings.market_data_timeout_seconds,
        max_retries=settings.market_data_max_retries,
    )
    try:
        provider = build_provider(settings, client)
        print(provider.capabilities().model_dump_json(indent=2))
        print((await provider.search_symbols("Apple", 3))[0].model_dump_json(indent=2))
        print((await provider.get_quote("AAPL")).model_dump_json(indent=2))
        candles = await provider.get_candles("AAPL", Interval.ONE_DAY, None, None, 5)
        print(candles.model_dump_json(indent=2))
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
