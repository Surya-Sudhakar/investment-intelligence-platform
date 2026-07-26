import asyncio

import httpx
import pytest

from app.core.exceptions import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from app.modules.market_data.http_client import MarketDataHttpClient


def test_http_client_success_auth_and_rate_limit() -> None:
    async def scenario() -> None:
        statuses = iter([200, 401, 429])

        def handler(request: httpx.Request) -> httpx.Response:
            status = next(statuses)
            return httpx.Response(
                status,
                json={"ok": True},
                headers={"Retry-After": "12"},
                request=request,
            )

        client = MarketDataHttpClient(
            timeout_seconds=1,
            max_retries=0,
            transport=httpx.MockTransport(handler),
        )
        assert await client.get_json("https://example.test", {}) == {"ok": True}
        with pytest.raises(ProviderAuthenticationError):
            await client.get_json("https://example.test", {})
        with pytest.raises(ProviderRateLimitError) as error:
            await client.get_json("https://example.test", {})
        assert error.value.details == {"retry_after_seconds": 12}
        await client.close()

    asyncio.run(scenario())


def test_http_client_retries_transient_failure() -> None:
    async def scenario() -> None:
        calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal calls
            calls += 1
            return httpx.Response(503 if calls == 1 else 200, json={"ok": True}, request=request)

        client = MarketDataHttpClient(
            timeout_seconds=1,
            max_retries=1,
            transport=httpx.MockTransport(handler),
        )
        assert await client.get_json("https://example.test", {}) == {"ok": True}
        assert calls == 2
        await client.close()

    asyncio.run(scenario())


def test_http_client_maps_timeout() -> None:
    async def scenario() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("timeout", request=request)

        client = MarketDataHttpClient(
            timeout_seconds=1,
            max_retries=0,
            transport=httpx.MockTransport(handler),
        )
        with pytest.raises(ProviderTimeoutError):
            await client.get_json("https://example.test", {})
        await client.close()

    asyncio.run(scenario())
