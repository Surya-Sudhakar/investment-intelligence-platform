import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from app.core.config import Settings
from app.modules.market_data.cache import TTLCache
from app.modules.market_data.schemas import DataStatus, Quote
from app.modules.market_data.service import MarketDataService


class QuoteProvider:
    name = "test"

    def __init__(self) -> None:
        self.calls: list[str] = []

    @staticmethod
    def provider_symbol(symbol: str) -> str:
        return "XAU/USD" if symbol == "XAUUSD" else symbol

    async def get_quote(self, symbol: str) -> Quote:
        self.calls.append(symbol)
        await asyncio.sleep(0)
        now = datetime.now(UTC)
        return Quote(
            symbol=symbol,
            price=Decimal("2400"),
            timestamp=now,
            received_at=now,
            provider=self.name,
            delayed=False,
            data_status=DataStatus.UNKNOWN,
            age_seconds=0,
        )


def test_quote_translates_provider_symbol_and_deduplicates_in_flight_requests() -> None:
    async def scenario() -> None:
        provider = QuoteProvider()
        service = MarketDataService(provider, TTLCache(), Settings())  # type: ignore[arg-type]
        first, second = await asyncio.gather(
            service.quote("XAUUSD"),
            service.quote("XAU/USD"),
        )
        assert provider.calls == ["XAU/USD"]
        assert first.symbol == "XAUUSD"
        assert second.symbol == "XAUUSD"
        assert second.cached is True

    asyncio.run(scenario())
