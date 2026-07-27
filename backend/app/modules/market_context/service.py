import asyncio
from datetime import UTC, datetime

from app.core.exceptions import MarketDataError
from app.modules.assets.schemas import (
    AssetIntelligenceResponse,
    AssetResolution,
    AssetType,
    EtfMetrics,
    EtfProfile,
    StockProfile,
)
from app.modules.assets.service import AssetIntelligenceService
from app.modules.market_context.calculation import (
    SIGNALS,
    aligned_relative_strength,
    classify_overall,
    performance,
    weighted_context,
)
from app.modules.market_context.config import (
    CONTEXT_CONFIG,
    ETF_WEIGHTS,
    GOLD_WEIGHTS,
    STOCK_WEIGHTS,
)
from app.modules.market_context.provider import MarketContextProvider
from app.modules.market_context.schemas import (
    AlignmentMetadata,
    AvailabilityStatus,
    AvailableValue,
    CommoditySection,
    ContextClassification,
    ContextFreshness,
    ContextHorizon,
    ContextReference,
    ContextReferences,
    EtfSection,
    IndustrySection,
    MarketContextAvailability,
    MarketContextResponse,
    MarketSection,
    PartialDataStatus,
    PerformanceObservation,
    ReferenceKind,
    RelativeStrengthObservation,
    RelativeStrengthSection,
    SectorSection,
)
from app.modules.market_data.cache import TTLCache
from app.modules.market_data.schemas import Candle, Interval
from app.modules.market_data.service import MarketDataService


def field[T](
    status: AvailabilityStatus,
    reason: str,
    value: T | None = None,
    alignment: AlignmentMetadata | None = None,
) -> AvailableValue[T]:
    return AvailableValue(status=status, value=value, reason=reason, alignment=alignment)


def available[T](value: T, reason: str = "Data is available.") -> AvailableValue[T]:
    return field(AvailabilityStatus.AVAILABLE, reason, value)


def unavailable[T](reason: str, alignment: AlignmentMetadata | None = None) -> AvailableValue[T]:
    return field(AvailabilityStatus.UNAVAILABLE, reason, alignment=alignment)


def not_applicable[T](reason: str) -> AvailableValue[T]:
    return field(AvailabilityStatus.NOT_APPLICABLE, reason)


def planned_phase8[T](reason: str) -> AvailableValue[T]:
    return field(AvailabilityStatus.PLANNED_PHASE8, reason)


class MarketContextService:
    def __init__(
        self,
        assets: AssetIntelligenceService,
        market_data: MarketDataService,
        context_provider: MarketContextProvider,
        cache: TTLCache,
        cache_ttl_seconds: int,
        partial_cache_ttl_seconds: int,
    ) -> None:
        self.assets = assets
        self.market_data = market_data
        self.context_provider = context_provider
        self.cache = cache
        self.cache_ttl_seconds = cache_ttl_seconds
        self.partial_cache_ttl_seconds = partial_cache_ttl_seconds

    async def get_context(self, symbol: str) -> MarketContextResponse:
        resolution = await self.assets.resolve_asset(symbol)
        cache_key = (
            f"market-context:{CONTEXT_CONFIG.methodology_version}:"
            f"{self.market_data.provider.name}:{resolution.symbol}"
        )
        cached = await self.cache.get(cache_key)
        if isinstance(cached, MarketContextResponse):
            return cached.model_copy(deep=True)

        asset = await self._asset_metadata(resolution)
        references = self.context_provider.references(resolution, asset)
        response = await self._build(resolution, asset, references)
        complete = response.overall_context.status is AvailabilityStatus.AVAILABLE
        ttl = self.cache_ttl_seconds if complete else self.partial_cache_ttl_seconds
        await self.cache.set(cache_key, response, ttl)
        return response

    async def _asset_metadata(
        self, resolution: AssetResolution
    ) -> AssetIntelligenceResponse | None:
        if resolution.asset_type is AssetType.GOLD:
            return None
        try:
            return await self.assets.get_intelligence(resolution.symbol)
        except MarketDataError:
            return None

    async def _build(
        self,
        resolution: AssetResolution,
        asset: AssetIntelligenceResponse | None,
        references: ContextReferences,
    ) -> MarketContextResponse:
        generated_at = datetime.now(UTC)
        asset_reference = ContextReference(
            symbol=resolution.provider_symbol,
            name=resolution.display_name or resolution.symbol,
            kind=ReferenceKind.COMMODITY
            if resolution.asset_type is AssetType.GOLD
            else ReferenceKind.ASSET,
        )
        named_references = {
            "asset": asset_reference,
            **{
                name: value
                for name, value in {
                    "market": references.market,
                    "sector": references.sector,
                    "industry": references.industry,
                    "benchmark": references.benchmark,
                    "silver": references.silver,
                    "commodity_index": references.commodity_index,
                }.items()
                if value is not None
            },
        }
        observations, series = await self._load_observations(named_references)
        warnings: list[str] = []
        support: list[str] = []

        if "asset" not in observations:
            warnings.append("Asset performance is unavailable because daily observations failed.")

        market = self._market_section(resolution, references, observations)
        sector, sector_name = self._sector_section(
            resolution.asset_type, asset, references, observations
        )
        industry, industry_name = self._industry_section(
            resolution.asset_type, asset, references, observations
        )
        relative = self._relative_section(resolution, asset_reference, references, series)
        commodity = self._commodity_section(
            resolution, asset_reference, references, observations, series
        )
        etf = self._etf_section(resolution, asset_reference, asset, references, series)

        components = self._components(resolution.asset_type, observations, relative, commodity, etf)
        weights = (
            STOCK_WEIGHTS
            if resolution.asset_type is AssetType.STOCK
            else GOLD_WEIGHTS
            if resolution.asset_type is AssetType.GOLD
            else ETF_WEIGHTS
        )
        context, coverage = weighted_context(components, weights)
        all_observations = list(observations.values())
        freshness, freshness_quality = self._freshness(all_observations, generated_at)
        sample_quality = (
            min(item.observations for item in all_observations) / CONTEXT_CONFIG.lookback_sessions
            if all_observations
            else 0
        )
        proxy_penalty = 5 if any(item.reference.is_proxy for item in all_observations) else 0
        confidence = max(
            0,
            min(
                100,
                round(coverage * 70 + freshness_quality * 20 + sample_quality * 10) - proxy_penalty,
            ),
        )

        for name, observation in observations.items():
            if name == "asset":
                support.append(
                    f"{resolution.symbol} moved {observation.return_percentage}% over "
                    f"{observation.observations} daily observations."
                )
        for label, value in (
            ("market", relative.versus_market),
            ("sector", relative.versus_sector),
            ("industry", relative.versus_industry),
        ):
            if value.status is AvailabilityStatus.AVAILABLE and value.value:
                support.append(
                    f"{resolution.symbol} performed "
                    f"{value.value.difference_percentage_points} percentage points versus "
                    f"the {label} reference."
                )
        if any(item.reference.is_proxy for item in all_observations):
            warnings.append("One or more comparisons use explicitly labelled proxy instruments.")
        if sector_name is None and resolution.asset_type is AssetType.STOCK:
            warnings.append("Sector metadata is unavailable from the configured provider.")
        if industry_name is None and resolution.asset_type is AssetType.STOCK:
            warnings.append("Industry metadata is unavailable from the configured provider.")
        for label, value in (
            ("market", relative.versus_market),
            ("sector", relative.versus_sector),
            ("industry", relative.versus_industry),
            ("silver", commodity.silver_comparison),
            ("ETF benchmark", etf.relative_performance),
        ):
            if value.alignment is not None and not value.alignment.alignment_sufficient:
                warnings.append(
                    f"Relative comparison with {label} is unavailable: "
                    f"{value.alignment.actual_overlap_count} common daily observations; "
                    f"{value.alignment.minimum_required} required."
                )

        overall = (
            available(context, "Calculated from the available weighted context components.")
            if context is not None
            else unavailable("Insufficient directional market-context components are available.")
        )
        statuses = self._availability(resolution.asset_type, observations, market, sector, industry)
        source_timestamp = (
            min(item.last_timestamp for item in all_observations) if all_observations else None
        )
        return MarketContextResponse(
            symbol=resolution.symbol,
            display_name=resolution.display_name or resolution.symbol,
            asset_type=resolution.asset_type,
            provider=self.market_data.provider.name,
            methodology_version=CONTEXT_CONFIG.methodology_version,
            horizon=ContextHorizon(lookback_sessions=CONTEXT_CONFIG.lookback_sessions),
            overall_context=overall,
            confidence=confidence,
            partial_data_status=(
                PartialDataStatus.UNAVAILABLE
                if overall.status is AvailabilityStatus.UNAVAILABLE
                else PartialDataStatus.PARTIAL
                if warnings or coverage < 1
                else PartialDataStatus.COMPLETE
            ),
            market=market,
            sector=sector,
            industry=industry,
            commodity=commodity,
            etf=etf,
            relative_strength=relative,
            supporting_observations=support,
            warnings=list(dict.fromkeys(warnings)),
            freshness=freshness,
            availability=statuses,
            source_timestamp=available(
                source_timestamp,
                "Oldest latest timestamp among contributing series.",
            )
            if source_timestamp
            else unavailable("No contributing source timestamp is available."),
            generated_at=generated_at,
        )

    async def _load_observations(
        self, references: dict[str, ContextReference]
    ) -> tuple[
        dict[str, PerformanceObservation],
        dict[str, list[Candle]],
    ]:
        async def load(
            name: str, reference: ContextReference
        ) -> tuple[str, PerformanceObservation | None, list[Candle]]:
            try:
                response = await self.market_data.candles(
                    reference.symbol,
                    Interval.ONE_DAY,
                    None,
                    None,
                    CONTEXT_CONFIG.requested_candles,
                )
            except MarketDataError:
                return name, None, []
            return (
                name,
                performance(
                    reference,
                    response.data.candles,
                    CONTEXT_CONFIG.lookback_sessions,
                    CONTEXT_CONFIG.minimum_sessions,
                ),
                response.data.candles,
            )

        loaded = await asyncio.gather(
            *(load(name, reference) for name, reference in references.items())
        )
        return (
            {name: value for name, value, _ in loaded if value is not None},
            {name: candles for name, _, candles in loaded if candles},
        )

    @staticmethod
    def _market_section(
        resolution: AssetResolution,
        references: ContextReferences,
        observations: dict[str, PerformanceObservation],
    ) -> MarketSection:
        market_reference = references.market or references.benchmark
        market_observation = observations.get("market") or observations.get("benchmark")
        if resolution.asset_type is AssetType.GOLD:
            return MarketSection(
                primary_exchange=not_applicable(
                    "An equity primary exchange is not applicable to gold spot."
                ),
                primary_market_index=not_applicable(
                    "An equity primary market index is not applicable to gold."
                ),
                reference=not_applicable("Gold uses the dedicated commodity-context section."),
                performance=not_applicable("Gold uses the dedicated commodity-context section."),
            )
        return MarketSection(
            primary_exchange=available(resolution.exchange)
            if resolution.exchange
            else unavailable("The provider did not identify a primary exchange."),
            primary_market_index=unavailable(
                "The provider did not supply an authoritative primary market index."
            ),
            reference=available(
                market_reference,
                "This is an explicitly labelled comparison reference.",
            )
            if market_reference
            else unavailable("No compatible market reference was identified."),
            performance=available(market_observation)
            if market_observation
            else unavailable("Market-reference daily observations are unavailable."),
        )

    @staticmethod
    def _sector_section(
        asset_type: AssetType,
        asset: AssetIntelligenceResponse | None,
        references: ContextReferences,
        observations: dict[str, PerformanceObservation],
    ) -> tuple[SectorSection, str | None]:
        if asset_type is not AssetType.STOCK:
            reason = "Sector context is not applicable to this asset type."
            return (
                SectorSection(
                    name=not_applicable(reason),
                    reference=not_applicable(reason),
                    performance=not_applicable(reason),
                    trend=not_applicable(reason),
                ),
                None,
            )
        profile = asset.profile if asset else None
        sector_name = profile.sector if isinstance(profile, StockProfile) else None
        observation = observations.get("sector")
        section = SectorSection(
            name=available(sector_name)
            if sector_name
            else unavailable("The provider did not supply sector metadata."),
            reference=available(references.sector, "Sector proxy; not a sector average.")
            if references.sector
            else unavailable("No reliable sector reference was identified."),
            performance=available(observation)
            if observation
            else unavailable("Sector-reference daily observations are unavailable."),
            trend=available(observation.classification)
            if observation
            else unavailable("Sector trend cannot be calculated without observations."),
        )
        return section, sector_name

    @staticmethod
    def _industry_section(
        asset_type: AssetType,
        asset: AssetIntelligenceResponse | None,
        references: ContextReferences,
        observations: dict[str, PerformanceObservation],
    ) -> tuple[IndustrySection, str | None]:
        if asset_type is not AssetType.STOCK:
            reason = "Industry context is not applicable to this asset type."
            return (
                IndustrySection(
                    name=not_applicable(reason),
                    reference=not_applicable(reason),
                    performance=not_applicable(reason),
                    trend=not_applicable(reason),
                ),
                None,
            )
        profile = asset.profile if asset else None
        industry_name = profile.industry if isinstance(profile, StockProfile) else None
        observation = observations.get("industry")
        return (
            IndustrySection(
                name=available(industry_name)
                if industry_name
                else unavailable("The provider did not supply industry metadata."),
                reference=available(references.industry)
                if references.industry
                else unavailable("No reliable industry reference was identified."),
                performance=available(observation)
                if observation
                else unavailable("Industry-reference daily observations are unavailable."),
                trend=available(observation.classification)
                if observation
                else unavailable("Industry trend cannot be calculated without observations."),
            ),
            industry_name,
        )

    @staticmethod
    def _relative_section(
        resolution: AssetResolution,
        asset_reference: ContextReference,
        references: ContextReferences,
        series: dict[str, list[Candle]],
    ) -> RelativeStrengthSection:
        def compare(
            name: str, reference: ContextReference | None
        ) -> AvailableValue[RelativeStrengthObservation]:
            if not reference:
                return unavailable(f"No {name} reference was identified.")
            asset_candles = series.get("asset", [])
            reference_candles = series.get(name, [])
            if not asset_candles or not reference_candles:
                return unavailable(
                    f"Asset and {name} observations are required for relative strength."
                )
            result, alignment = aligned_relative_strength(
                resolution.symbol,
                asset_reference,
                asset_candles,
                reference,
                reference_candles,
                CONTEXT_CONFIG.lookback_sessions,
                CONTEXT_CONFIG.minimum_sessions,
            )
            if result is None:
                return unavailable(
                    "Insufficient common daily observations for aligned relative strength.",
                    alignment,
                )
            return field(
                AvailabilityStatus.AVAILABLE,
                "Calculated from closes on actual shared daily dates.",
                result,
                alignment,
            )

        return RelativeStrengthSection(
            versus_market=compare("market", references.market),
            versus_sector=compare("sector", references.sector),
            versus_industry=compare("industry", references.industry),
        )

    @staticmethod
    def _commodity_section(
        resolution: AssetResolution,
        asset_reference: ContextReference,
        references: ContextReferences,
        observations: dict[str, PerformanceObservation],
        series: dict[str, list[Candle]],
    ) -> CommoditySection:
        if resolution.asset_type is not AssetType.GOLD:
            reason = "Commodity context is not applicable to this asset type."
            return CommoditySection(
                precious_metals_trend=not_applicable(reason),
                silver_comparison=not_applicable(reason),
                commodity_index_trend=not_applicable(reason),
                safe_haven_demand_trend=not_applicable(reason),
                commodity_market_alignment=not_applicable(reason),
            )
        gold = observations.get("asset")
        silver = observations.get("silver")
        comparison = None
        silver_alignment = None
        if references.silver and series.get("asset") and series.get("silver"):
            comparison, silver_alignment = aligned_relative_strength(
                resolution.symbol,
                asset_reference,
                series["asset"],
                references.silver,
                series["silver"],
                CONTEXT_CONFIG.lookback_sessions,
                CONTEXT_CONFIG.minimum_sessions,
            )
        alignment = None
        if gold and silver:
            average_signal = (SIGNALS[gold.classification] + SIGNALS[silver.classification]) / 2
            alignment = classify_overall(average_signal)
        return CommoditySection(
            precious_metals_trend=available(gold.classification)
            if gold
            else unavailable("Gold daily observations are unavailable."),
            silver_comparison=field(
                AvailabilityStatus.AVAILABLE,
                "Calculated from gold and silver closes on shared daily dates.",
                comparison,
                silver_alignment,
            )
            if comparison
            else unavailable(
                "Silver and gold require sufficient common daily observations.",
                silver_alignment,
            ),
            commodity_index_trend=unavailable(
                "No compatible daily commodity-index series was supplied."
            ),
            safe_haven_demand_trend=planned_phase8(
                "Safe-haven demand requires macroeconomic or event context reserved for Phase 8."
            ),
            commodity_market_alignment=available(alignment)
            if alignment
            else unavailable("Gold and silver observations are required for alignment."),
        )

    @staticmethod
    def _etf_section(
        resolution: AssetResolution,
        asset_reference: ContextReference,
        asset: AssetIntelligenceResponse | None,
        references: ContextReferences,
        series: dict[str, list[Candle]],
    ) -> EtfSection:
        if resolution.asset_type is not AssetType.ETF:
            reason = "ETF context is not applicable to this asset type."
            return EtfSection(
                etf_category=not_applicable(reason),
                fund_category=not_applicable(reason),
                benchmark_index=not_applicable(reason),
                regional_exposure=not_applicable(reason),
                sector_concentration=not_applicable(reason),
                relative_performance=not_applicable(reason),
            )
        profile = asset.profile if asset else None
        metrics = asset.metrics if asset else None
        category = profile.fund_category if isinstance(profile, EtfProfile) else None
        regions = (
            [item.name for item in metrics.geographic_allocation]
            if isinstance(metrics, EtfMetrics) and metrics.geographic_allocation
            else None
        )
        sectors = (
            [item.name for item in metrics.sector_allocation]
            if isinstance(metrics, EtfMetrics) and metrics.sector_allocation
            else None
        )
        comparison = None
        benchmark_alignment = None
        if references.benchmark and series.get("asset") and series.get("benchmark"):
            comparison, benchmark_alignment = aligned_relative_strength(
                resolution.symbol,
                asset_reference,
                series["asset"],
                references.benchmark,
                series["benchmark"],
                CONTEXT_CONFIG.lookback_sessions,
                CONTEXT_CONFIG.minimum_sessions,
            )
        return EtfSection(
            etf_category=available(category)
            if category
            else unavailable("The provider did not supply an ETF category."),
            fund_category=available(category)
            if category
            else unavailable("The provider did not supply a fund category."),
            benchmark_index=available(references.benchmark)
            if references.benchmark
            else unavailable("The provider did not identify an authoritative ETF benchmark."),
            regional_exposure=available(regions)
            if regions
            else unavailable("Regional allocation data is unavailable."),
            sector_concentration=available(sectors)
            if sectors
            else unavailable("Sector-allocation data is unavailable."),
            relative_performance=field(
                AvailabilityStatus.AVAILABLE,
                "Calculated from ETF and benchmark closes on shared daily dates.",
                comparison,
                benchmark_alignment,
            )
            if comparison
            else unavailable(
                "ETF and benchmark require sufficient common daily observations.",
                benchmark_alignment,
            ),
        )

    @staticmethod
    def _components(
        asset_type: AssetType,
        observations: dict[str, PerformanceObservation],
        relative: RelativeStrengthSection,
        commodity: CommoditySection,
        etf: EtfSection,
    ) -> dict[str, ContextClassification]:
        components: dict[str, ContextClassification] = {}
        if asset_type is AssetType.STOCK:
            for name, key in (
                ("market_trend", "market"),
                ("sector_trend", "sector"),
                ("industry_trend", "industry"),
            ):
                if key in observations:
                    components[name] = observations[key].classification
            for name, value in (
                ("asset_vs_market", relative.versus_market),
                ("asset_vs_sector", relative.versus_sector),
                ("asset_vs_industry", relative.versus_industry),
            ):
                if value.status is AvailabilityStatus.AVAILABLE and value.value:
                    components[name] = value.value.classification
        elif asset_type is AssetType.GOLD:
            if "asset" in observations:
                components["gold_trend"] = observations["asset"].classification
            if "silver" in observations:
                components["silver_trend"] = observations["silver"].classification
            if (
                commodity.silver_comparison.status is AvailabilityStatus.AVAILABLE
                and commodity.silver_comparison.value
            ):
                components["gold_vs_silver"] = commodity.silver_comparison.value.classification
            if (
                commodity.commodity_market_alignment.status is AvailabilityStatus.AVAILABLE
                and commodity.commodity_market_alignment.value
            ):
                components["commodity_alignment"] = commodity.commodity_market_alignment.value
        elif asset_type is AssetType.ETF:
            if "benchmark" in observations:
                components["benchmark_trend"] = observations["benchmark"].classification
            if (
                etf.relative_performance.status is AvailabilityStatus.AVAILABLE
                and etf.relative_performance.value
            ):
                components["etf_vs_benchmark"] = etf.relative_performance.value.classification
        return components

    @staticmethod
    def _freshness(
        observations: list[PerformanceObservation], generated_at: datetime
    ) -> tuple[ContextFreshness, float]:
        if not observations:
            return (
                ContextFreshness(
                    status=AvailabilityStatus.UNAVAILABLE,
                    reason="No source observations are available.",
                ),
                0,
            )
        latest_points = [item.last_timestamp for item in observations]
        oldest = min(latest_points)
        newest = max(latest_points)
        age_days = max(0, (generated_at - oldest).days)
        if age_days <= CONTEXT_CONFIG.current_max_age_days:
            state, quality, reason = "CURRENT", 1.0, "All contributing series are current."
        elif age_days < CONTEXT_CONFIG.stale_age_days:
            state, quality, reason = "RECENT", 0.6, "Some contributing observations are delayed."
        else:
            state, quality, reason = "STALE", 0.2, "Contributing observations are stale."
        return (
            ContextFreshness(
                status=AvailabilityStatus.AVAILABLE,
                state=state,
                oldest_source_timestamp=oldest,
                newest_source_timestamp=newest,
                age_days=age_days,
                reason=reason,
            ),
            quality,
        )

    @staticmethod
    def _availability(
        asset_type: AssetType,
        observations: dict[str, PerformanceObservation],
        market: MarketSection,
        sector: SectorSection,
        industry: IndustrySection,
    ) -> MarketContextAvailability:
        return MarketContextAvailability(
            asset_performance=AvailabilityStatus.AVAILABLE
            if "asset" in observations
            else AvailabilityStatus.UNAVAILABLE,
            market=market.performance.status,
            sector=sector.performance.status
            if asset_type is AssetType.STOCK
            else AvailabilityStatus.NOT_APPLICABLE,
            industry=industry.performance.status
            if asset_type is AssetType.STOCK
            else AvailabilityStatus.NOT_APPLICABLE,
            relative_strength=AvailabilityStatus.AVAILABLE
            if any(name in observations for name in ("market", "sector", "industry", "benchmark"))
            else AvailabilityStatus.UNAVAILABLE,
            commodity=AvailabilityStatus.AVAILABLE
            if asset_type is AssetType.GOLD and "asset" in observations
            else AvailabilityStatus.NOT_APPLICABLE
            if asset_type is not AssetType.GOLD
            else AvailabilityStatus.UNAVAILABLE,
            etf=AvailabilityStatus.AVAILABLE
            if asset_type is AssetType.ETF and "benchmark" in observations
            else AvailabilityStatus.NOT_APPLICABLE
            if asset_type is not AssetType.ETF
            else AvailabilityStatus.UNAVAILABLE,
        )
