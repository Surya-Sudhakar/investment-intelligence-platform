import asyncio

import httpx

from app.modules.market_data.http_client import MarketDataHttpClient
from app.modules.market_data.schemas import Interval
from app.modules.market_data.twelve_data import TwelveDataProvider


def provider_for(responses: dict[str, dict[str, object]]) -> TwelveDataProvider:
    def handler(request: httpx.Request) -> httpx.Response:
        endpoint = request.url.path.rsplit("/", 1)[-1]
        return httpx.Response(200, json=responses[endpoint], request=request)

    return TwelveDataProvider(
        "test-key",
        "https://example.test",
        MarketDataHttpClient(
            timeout_seconds=1,
            max_retries=0,
            transport=httpx.MockTransport(handler),
        ),
    )


def test_quote_and_daily_candles_are_normalized() -> None:
    async def scenario() -> None:
        provider = provider_for(
            {
                "quote": {
                    "symbol": "AAPL",
                    "timestamp": 1784908800,
                    "open": "210",
                    "high": "215",
                    "low": "209",
                    "close": "214.50",
                    "previous_close": "211",
                    "change": "3.5",
                    "percent_change": "1.65",
                    "volume": "123",
                    "is_market_open": True,
                },
                "time_series": {
                    "meta": {"exchange_timezone": "America/New_York"},
                    "values": [
                        {
                            "datetime": "2026-07-23",
                            "open": "210",
                            "high": "215",
                            "low": "209",
                            "close": "214.50",
                            "volume": "123",
                        }
                    ],
                },
            }
        )
        quote = await provider.get_quote("AAPL")
        candles = await provider.get_candles("AAPL", Interval.ONE_DAY, None, None, 260)
        assert quote.provider == "twelve_data"
        assert quote.market_open is True
        assert str(quote.price) == "214.50"
        assert len(candles.candles) == 1
        assert candles.source_timezone == "America/New_York"
        await provider.client.close()

    asyncio.run(scenario())


def test_search_and_details_are_normalized() -> None:
    async def scenario() -> None:
        provider = provider_for(
            {
                "symbol_search": {
                    "data": [
                        {
                            "symbol": "AAPL",
                            "instrument_name": "Apple Inc",
                            "instrument_type": "Common Stock",
                            "exchange": "NASDAQ",
                            "currency": "USD",
                            "country": "United States",
                        }
                    ]
                },
                "stocks": {
                    "data": [
                        {
                            "symbol": "AAPL",
                            "name": "Apple Inc",
                            "exchange": "NASDAQ",
                            "currency": "USD",
                            "country": "United States",
                            "timezone": "America/New_York",
                        }
                    ]
                },
            }
        )
        results = await provider.search_symbols("Apple", 10)
        details = await provider.get_symbol_details("AAPL")
        assert results[0].symbol == "AAPL"
        assert details.timezone == "America/New_York"
        await provider.client.close()

    asyncio.run(scenario())
