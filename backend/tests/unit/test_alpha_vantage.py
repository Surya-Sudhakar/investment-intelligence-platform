import asyncio

import httpx
import pytest

from app.core.exceptions import (
    ProviderConfigurationError,
    ProviderInvalidResponseError,
    ProviderRateLimitError,
)
from app.modules.market_data.alpha_vantage import AlphaVantageProvider
from app.modules.market_data.http_client import MarketDataHttpClient
from app.modules.market_data.schemas import Interval


def provider_for(payload: dict[str, object]) -> AlphaVantageProvider:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload, request=request)

    return AlphaVantageProvider(
        "test-key",
        "https://example.test",
        MarketDataHttpClient(
            timeout_seconds=1,
            max_retries=0,
            transport=httpx.MockTransport(handler),
        ),
    )


def test_search_filters_assets_and_duplicates() -> None:
    async def scenario() -> None:
        provider = provider_for(
            {
                "bestMatches": [
                    {
                        "1. symbol": "AAPL",
                        "2. name": "Apple",
                        "3. type": "Equity",
                        "4. region": "United States",
                        "8. currency": "USD",
                    },
                    {
                        "1. symbol": "AAPL",
                        "2. name": "Apple duplicate",
                        "3. type": "Equity",
                    },
                    {"1. symbol": "FUND", "2. name": "Fund", "3. type": "ETF"},
                ]
            }
        )
        results = await provider.search_symbols("apple", 10)
        assert [item.symbol for item in results] == ["AAPL"]
        await provider.client.close()

    asyncio.run(scenario())


def test_candles_sort_deduplicate_and_reject_invalid_rows() -> None:
    async def scenario() -> None:
        provider = provider_for(
            {
                "Meta Data": {"5. Time Zone": "UTC"},
                "Time Series (Daily)": {
                    "2026-07-23": {
                        "1. open": "10",
                        "2. high": "12",
                        "3. low": "9",
                        "4. close": "11",
                        "5. volume": "0",
                    },
                    "2026-07-22": {
                        "1. open": "10",
                        "2. high": "8",
                        "3. low": "9",
                        "4. close": "11",
                        "5. volume": "-1",
                    },
                },
            }
        )
        batch = await provider.get_candles("AAPL", Interval.ONE_DAY, None, None, 10)
        assert len(batch.candles) == 1
        assert batch.candles[0].volume == 0
        assert batch.received_count == 2
        assert batch.rejected_count == 1
        assert batch.candles == sorted(batch.candles, key=lambda candle: candle.time)
        await provider.client.close()

    asyncio.run(scenario())


def test_quote_normalization_and_age() -> None:
    async def scenario() -> None:
        provider = provider_for(
            {
                "Global Quote": {
                    "01. symbol": "AAPL",
                    "02. open": "210",
                    "03. high": "215",
                    "04. low": "209",
                    "05. price": "214.50",
                    "06. volume": "123",
                    "07. latest trading day": "2026-07-23",
                    "08. previous close": "211",
                    "09. change": "3.5",
                    "10. change percent": "1.65%",
                }
            }
        )
        quote = await provider.get_quote("AAPL")
        assert str(quote.price) == "214.50"
        assert quote.bid is None and quote.ask is None and quote.spread is None
        assert quote.delayed is True
        assert quote.age_seconds >= 0
        await provider.client.close()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "payload",
    [
        {"Global Quote": {"05. price": "0", "07. latest trading day": "2026-07-23"}},
        {"Global Quote": {"05. price": "10"}},
        {"Global Quote": {"07. latest trading day": "2026-07-23"}},
    ],
)
def test_quote_rejects_invalid_required_fields(payload: dict[str, object]) -> None:
    async def scenario() -> None:
        provider = provider_for(payload)
        with pytest.raises(ProviderInvalidResponseError):
            await provider.get_quote("AAPL")
        await provider.client.close()

    asyncio.run(scenario())


def test_provider_note_maps_rate_limit() -> None:
    async def scenario() -> None:
        provider = provider_for({"Note": "API call frequency exceeded"})
        with pytest.raises(ProviderRateLimitError):
            await provider.search_symbols("apple", 10)
        await provider.client.close()

    asyncio.run(scenario())


def test_missing_api_key_blocks_provider_calls_and_health_reports_unconfigured() -> None:
    async def scenario() -> None:
        provider = AlphaVantageProvider(
            None,
            "https://example.test",
            MarketDataHttpClient(timeout_seconds=1, max_retries=0),
        )
        with pytest.raises(ProviderConfigurationError):
            await provider.search_symbols("apple", 10)
        health = await provider.health_check()
        assert health.configured is False
        assert health.reachable is False
        await provider.client.close()

    asyncio.run(scenario())
