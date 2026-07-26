import asyncio

from app.modules.market_data.cache import TTLCache


def test_cache_hit_miss_expiration_and_disabled() -> None:
    async def scenario() -> None:
        cache = TTLCache()
        assert await cache.get("missing") is None
        await cache.set("key", "value", 10)
        assert await cache.get("key") == "value"
        await cache.set("expired", "value", 0)
        assert await cache.get("expired") is None
        disabled = TTLCache(enabled=False)
        await disabled.set("key", "value", 10)
        assert await disabled.get("key") is None

    asyncio.run(scenario())


def test_cache_keys_are_separate() -> None:
    async def scenario() -> None:
        cache = TTLCache()
        await cache.set("quote:AAPL", 1, 10)
        await cache.set("quote:MSFT", 2, 10)
        assert await cache.get("quote:AAPL") == 1
        assert await cache.get("quote:MSFT") == 2

    asyncio.run(scenario())
