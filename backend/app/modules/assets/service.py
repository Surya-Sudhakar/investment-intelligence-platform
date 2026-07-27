from datetime import UTC, datetime

from app.core.config import Settings
from app.core.exceptions import MarketDataError, UnsupportedAssetError
from app.modules.assets.classification import classify_fundamentals
from app.modules.assets.provider import AssetDataProvider
from app.modules.assets.schemas import (
    AssetAvailability,
    AssetIntelligenceResponse,
    AssetResolution,
    AssetType,
    GoldMetrics,
    GoldProfile,
    ProviderAssetData,
)
from app.modules.intelligence.freshness import classify_freshness
from app.modules.intelligence.schemas import MarketState
from app.modules.intelligence.service import IntelligenceService
from app.modules.market_data.cache import TTLCache
from app.modules.market_data.service import MarketDataService


class AssetIntelligenceService:
    def __init__(
        self,
        provider: AssetDataProvider,
        market_data: MarketDataService,
        intelligence: IntelligenceService,
        cache: TTLCache,
        settings: Settings,
    ) -> None:
        self.provider = provider
        self.market_data = market_data
        self.intelligence = intelligence
        self.cache = cache
        self.settings = settings

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        canonical = normalized.replace("/", "").replace("-", "")
        return "XAUUSD" if canonical == "XAUUSD" else MarketDataService.normalize_symbol(normalized)

    async def _resolve(self, symbol: str) -> AssetResolution:
        key = f"asset:classification:{symbol}"
        cached = await self.cache.get(key)
        if isinstance(cached, AssetResolution):
            return cached
        resolution = await self.provider.resolve_asset(symbol)
        await self.cache.set(key, resolution, self.settings.asset_classification_cache_ttl_seconds)
        return resolution

    async def resolve_asset(self, symbol: str) -> AssetResolution:
        canonical = self.normalize_symbol(symbol)
        resolution = await self._resolve(canonical)
        if resolution.asset_type is AssetType.UNKNOWN:
            raise UnsupportedAssetError(canonical)
        return resolution

    async def _provider_data(self, resolution: AssetResolution) -> ProviderAssetData:
        key = f"asset:data:{self.provider.name}:{resolution.symbol}"
        cached = await self.cache.get(key)
        if isinstance(cached, ProviderAssetData):
            return cached
        data = await self.provider.get_asset_data(resolution)
        ttl = (
            self.settings.asset_fundamentals_cache_ttl_seconds
            if resolution.asset_type is AssetType.STOCK
            else self.settings.asset_profile_cache_ttl_seconds
        )
        await self.cache.set(key, data, ttl)
        return data

    async def get_intelligence(self, symbol: str) -> AssetIntelligenceResponse:
        resolution = await self.resolve_asset(symbol)
        data = await self._provider_data(resolution)
        generated_at = datetime.now(UTC)
        warnings = list(data.warnings)
        source_timestamp = None
        freshness = None
        market_state = MarketState.UNKNOWN
        gold_metrics = None
        technical_available = False

        if resolution.asset_type is AssetType.GOLD:
            try:
                snapshot = await self.intelligence.snapshot(resolution.provider_symbol)
                source_timestamp = snapshot.quote.timestamp
                freshness = snapshot.freshness
                market_state = snapshot.market_status.state
                gold_metrics = GoldMetrics(
                    current_price=snapshot.quote.price,
                    trading_status=market_state,
                    high_52_week=snapshot.indicators.high_52_week,
                    low_52_week=snapshot.indicators.low_52_week,
                    recent_volatility=snapshot.volatility,
                    technical_snapshot_reference=f"/api/v1/intelligence/{resolution.symbol}",
                )
                technical_available = True
            except MarketDataError:
                gold_metrics = data.gold_metrics or GoldMetrics()
                source_timestamp = data.source_timestamp
                warnings.append(
                    "Gold technical observations are unavailable from the configured provider."
                )
        else:
            try:
                quote = await self.market_data.quote(resolution.provider_symbol)
                source_timestamp = quote.timestamp
                market_state = (
                    MarketState.OPEN
                    if quote.market_open is True
                    else MarketState.CLOSED
                    if quote.market_open is False
                    else MarketState.UNKNOWN
                )
                freshness = classify_freshness(
                    source_timestamp=quote.timestamp,
                    received_at=quote.received_at,
                    provider_delayed=quote.delayed,
                    market_status=market_state,
                    provider_reachable=True,
                    live_threshold_seconds=self.settings.intelligence_live_threshold_seconds,
                    stale_threshold_seconds=self.settings.intelligence_stale_threshold_seconds,
                    evaluated_at=generated_at,
                )
            except MarketDataError:
                warnings.append("Current price and freshness information are unavailable.")

        stock_metrics = data.stock_metrics
        classification = classify_fundamentals(stock_metrics) if stock_metrics else None
        if classification and classification.overall.value == "UNAVAILABLE":
            warnings.append("Insufficient fundamental metrics for an overall condition.")

        if freshness and freshness.state.value == "STALE":
            warnings.append("The latest market observation is stale.")

        profile = (
            data.stock_profile
            if resolution.asset_type is AssetType.STOCK
            else data.etf_profile
            if resolution.asset_type is AssetType.ETF
            else GoldProfile()
        )
        metrics = (
            stock_metrics
            if resolution.asset_type is AssetType.STOCK
            else data.etf_metrics
            if resolution.asset_type is AssetType.ETF
            else gold_metrics
        )
        return AssetIntelligenceResponse(
            symbol=resolution.symbol,
            display_name=resolution.display_name,
            asset_type=resolution.asset_type,
            exchange=resolution.exchange,
            currency=resolution.currency,
            provider=self.provider.name,
            source_timestamp=source_timestamp,
            generated_at=generated_at,
            freshness=freshness,
            profile=profile,
            metrics=metrics,
            classification=classification,
            warnings=list(dict.fromkeys(warnings)),
            availability=AssetAvailability(
                profile=profile is not None,
                metrics=metrics is not None,
                fundamentals=stock_metrics is not None,
                holdings=bool(data.etf_metrics and data.etf_metrics.top_holdings),
                allocations=bool(
                    data.etf_metrics
                    and (
                        data.etf_metrics.sector_allocation or data.etf_metrics.geographic_allocation
                    )
                ),
                technical_snapshot=technical_available,
            ),
        )
