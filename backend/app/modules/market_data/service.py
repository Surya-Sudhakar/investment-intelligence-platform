import re
from datetime import UTC, datetime

from app.core.config import Settings
from app.core.exceptions import InvalidSymbolError
from app.modules.market_data.cache import TTLCache
from app.modules.market_data.provider import MarketDataProvider
from app.modules.market_data.schemas import (
    CandleResponse,
    CandleResponseData,
    DataStatus,
    Interval,
    ProviderCapabilities,
    ProviderHealth,
    Quote,
    SymbolDetails,
    SymbolSearchResult,
)

SYMBOL_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,19}$")


class MarketDataService:
    def __init__(
        self,
        provider: MarketDataProvider,
        cache: TTLCache,
        settings: Settings,
    ) -> None:
        self.provider = provider
        self.cache = cache
        self.settings = settings

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not SYMBOL_PATTERN.fullmatch(normalized):
            raise InvalidSymbolError()
        return normalized

    def capabilities(self) -> ProviderCapabilities:
        return self.provider.capabilities()

    async def health(self) -> ProviderHealth:
        return await self.provider.health_check()

    async def search_symbols(self, query: str, limit: int) -> list[SymbolSearchResult]:
        normalized = " ".join(query.strip().split())
        key = f"search:{normalized.casefold()}:{limit}"
        cached = await self.cache.get(key)
        if isinstance(cached, list):
            return cached
        results = await self.provider.search_symbols(normalized, limit)
        unique = {item.symbol: item for item in results if item.asset_type == "stock"}
        output = [unique[symbol] for symbol in sorted(unique)][:limit]
        await self.cache.set(key, output, self.settings.market_data_symbol_cache_ttl_seconds)
        return output

    async def symbol_details(self, symbol: str) -> SymbolDetails:
        normalized = self.normalize_symbol(symbol)
        key = f"details:{normalized}"
        cached = await self.cache.get(key)
        if isinstance(cached, SymbolDetails):
            return cached
        details = await self.provider.get_symbol_details(normalized)
        await self.cache.set(key, details, self.settings.market_data_symbol_cache_ttl_seconds)
        return details

    async def candles(
        self,
        symbol: str,
        interval: Interval,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> CandleResponse:
        normalized = self.normalize_symbol(symbol)
        start_key = start.isoformat() if start else "-"
        end_key = end.isoformat() if end else "-"
        key = f"candles:{normalized}:{interval.value}:{start_key}:{end_key}:{limit}"
        cached = await self.cache.get(key)
        if isinstance(cached, CandleResponse):
            copied = cached.model_copy(deep=True)
            copied.data.cached = True
            copied.data.data_status = DataStatus.CACHED
            for candle in copied.data.candles:
                candle.data_status = DataStatus.CACHED
            return copied
        batch = await self.provider.get_candles(normalized, interval, start, end, limit)
        status = batch.candles[0].data_status if batch.candles else DataStatus.UNKNOWN
        response = CandleResponse(
            data=CandleResponseData(
                symbol=normalized,
                interval=interval,
                candles=batch.candles,
                provider=self.provider.name,
                count=len(batch.candles),
                received_count=batch.received_count,
                rejected_count=batch.rejected_count,
                requested_at=datetime.now(UTC),
                source_timezone=batch.source_timezone,
                data_status=status,
                cached=False,
            )
        )
        await self.cache.set(key, response, self.settings.market_data_candle_cache_ttl_seconds)
        return response

    async def quote(self, symbol: str) -> Quote:
        normalized = self.normalize_symbol(symbol)
        key = f"quote:{normalized}"
        cached = await self.cache.get(key)
        if isinstance(cached, Quote):
            copied = cached.model_copy(deep=True)
            copied.cached = True
            copied.data_status = DataStatus.CACHED
            return copied
        quote = await self.provider.get_quote(normalized)
        await self.cache.set(key, quote, self.settings.market_data_quote_cache_ttl_seconds)
        return quote
