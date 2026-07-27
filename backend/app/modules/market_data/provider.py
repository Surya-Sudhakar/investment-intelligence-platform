from collections.abc import AsyncIterator
from datetime import datetime
from typing import Protocol

from app.modules.market_data.schemas import (
    Interval,
    MarketStatus,
    ProviderCandleBatch,
    ProviderCapabilities,
    ProviderHealth,
    Quote,
    SymbolDetails,
    SymbolSearchResult,
)


class MarketDataProvider(Protocol):
    @property
    def name(self) -> str: ...

    async def search_symbols(self, query: str, limit: int) -> list[SymbolSearchResult]: ...

    async def get_symbol_details(self, symbol: str) -> SymbolDetails: ...

    async def get_candles(
        self,
        symbol: str,
        interval: Interval,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> ProviderCandleBatch: ...

    async def get_quote(self, symbol: str) -> Quote: ...

    async def get_market_status(self, symbol: str | None = None) -> MarketStatus: ...

    def provider_symbol(self, symbol: str) -> str:
        """Translate a canonical public symbol into the provider's notation."""
        ...

    def capabilities(self) -> ProviderCapabilities: ...

    async def health_check(self) -> ProviderHealth: ...

    def stream_prices(self, symbols: list[str]) -> AsyncIterator[Quote]:
        """Future-compatible contract; implementations raise NotImplementedError in Phase 2."""
        ...


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, MarketDataProvider] = {}

    def register(self, provider: MarketDataProvider) -> None:
        self._providers[provider.name] = provider

    def get(self, name: str) -> MarketDataProvider:
        from app.core.exceptions import ProviderConfigurationError

        try:
            return self._providers[name]
        except KeyError as exc:
            raise ProviderConfigurationError() from exc

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))
