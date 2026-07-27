import asyncio
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.modules.assets.schemas import (
    AssetAvailability,
    AssetIntelligenceResponse,
    AssetResolution,
    AssetType,
    EtfMetrics,
    EtfProfile,
    StockProfile,
)
from app.modules.market_context.references import ConfiguredContextProvider
from app.modules.market_context.schemas import AvailabilityStatus
from app.modules.market_context.service import MarketContextService
from app.modules.market_data.cache import TTLCache
from app.modules.market_data.schemas import (
    Candle,
    CandleResponse,
    CandleResponseData,
    DataStatus,
    Interval,
)


class FakeAssets:
    def __init__(self, asset_type: AssetType) -> None:
        self.asset_type = asset_type

    async def resolve_asset(self, symbol: str) -> AssetResolution:
        canonical = symbol.replace("/", "").upper()
        return AssetResolution(
            symbol=canonical,
            provider_symbol="XAU/USD" if self.asset_type is AssetType.GOLD else canonical,
            display_name="Test asset",
            asset_type=self.asset_type,
            exchange="NASDAQ" if self.asset_type is not AssetType.GOLD else None,
            currency="USD",
        )

    async def get_intelligence(self, symbol: str) -> AssetIntelligenceResponse:
        profile = (
            StockProfile(
                company_name="Test Inc.",
                sector="Technology",
                industry="Software",
            )
            if self.asset_type is AssetType.STOCK
            else EtfProfile(fund_name="Test ETF", fund_category="Large blend")
        )
        metrics = EtfMetrics() if self.asset_type is AssetType.ETF else None
        return AssetIntelligenceResponse(
            symbol=symbol,
            asset_type=self.asset_type,
            provider="test",
            generated_at=datetime.now(UTC),
            profile=profile,
            metrics=metrics,
            availability=AssetAvailability(profile=True),
        )


class FakeProvider:
    name = "test"


class FakeMarketData:
    provider = FakeProvider()

    def __init__(
        self,
        empty: bool = False,
        age_days: int = 0,
        reference_count: int = 20,
    ) -> None:
        self.calls = 0
        self.empty = empty
        self.age_days = age_days
        self.reference_count = reference_count

    async def candles(
        self,
        symbol: str,
        interval: Interval,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> CandleResponse:
        del start, end
        self.calls += 1
        now = datetime.now(UTC) - timedelta(days=19 + self.age_days)
        values = []
        if not self.empty:
            step = Decimal("2") if symbol in {"AAPL", "XAU/USD"} else Decimal("1")
            count = 20 if symbol in {"AAPL", "QQQ", "XAU/USD"} else self.reference_count
            for index in range(count):
                price = Decimal("100") + step * index
                timestamp = now + timedelta(days=index)
                values.append(
                    Candle(
                        symbol=symbol,
                        interval=interval,
                        time=timestamp,
                        open=price,
                        high=price + 1,
                        low=price - 1,
                        close=price,
                        volume=100,
                        is_complete=True,
                        provider="test",
                        source_timestamp=timestamp,
                        received_at=timestamp,
                        data_status=DataStatus.END_OF_DAY,
                    )
                )
        return CandleResponse(
            data=CandleResponseData(
                symbol=symbol,
                interval=interval,
                candles=values,
                provider="test",
                count=len(values),
                received_count=len(values),
                rejected_count=0,
                requested_at=datetime.now(UTC),
                source_timezone="UTC",
                data_status=DataStatus.END_OF_DAY,
                cached=False,
            )
        )


def make_service(
    asset_type: AssetType,
    empty: bool = False,
    age_days: int = 0,
    reference_count: int = 20,
) -> tuple[MarketContextService, FakeMarketData]:
    market = FakeMarketData(empty, age_days, reference_count)
    target = MarketContextService(
        FakeAssets(asset_type),  # type: ignore[arg-type]
        market,  # type: ignore[arg-type]
        ConfiguredContextProvider(),
        TTLCache(),
        300,
        60,
    )
    return target, market


def test_stock_context_and_final_response_cache() -> None:
    target, market = make_service(AssetType.STOCK)
    first = asyncio.run(target.get_context("AAPL"))
    calls = market.calls
    second = asyncio.run(target.get_context("AAPL"))

    assert first.market.reference.status is AvailabilityStatus.AVAILABLE
    assert first.sector.name.value == "Technology"
    assert first.relative_strength.versus_market.status is AvailabilityStatus.AVAILABLE
    assert first.industry.reference.status is AvailabilityStatus.UNAVAILABLE
    assert first.overall_context.status is AvailabilityStatus.AVAILABLE
    assert second.symbol == "AAPL"
    assert market.calls == calls


def test_gold_context_marks_phase8_and_non_applicable_fields() -> None:
    target, _ = make_service(AssetType.GOLD)
    result = asyncio.run(target.get_context("XAU/USD"))

    assert result.commodity.silver_comparison.status is AvailabilityStatus.AVAILABLE
    assert result.commodity.safe_haven_demand_trend.status is AvailabilityStatus.PLANNED_PHASE8
    assert result.sector.name.status is AvailabilityStatus.NOT_APPLICABLE
    assert result.etf.etf_category.status is AvailabilityStatus.NOT_APPLICABLE
    assert result.market.primary_market_index.status is AvailabilityStatus.NOT_APPLICABLE


def test_etf_returns_clean_partial_context_without_benchmark() -> None:
    target, _ = make_service(AssetType.ETF)
    result = asyncio.run(target.get_context("QQQ"))

    assert result.etf.fund_category.value == "Large blend"
    assert result.etf.benchmark_index.status is AvailabilityStatus.UNAVAILABLE
    assert result.overall_context.status is AvailabilityStatus.UNAVAILABLE
    assert result.availability.etf is AvailabilityStatus.UNAVAILABLE


def test_missing_provider_data_is_structured_and_reduces_confidence() -> None:
    target, _ = make_service(AssetType.STOCK, empty=True)
    result = asyncio.run(target.get_context("AAPL"))

    assert result.overall_context.status is AvailabilityStatus.UNAVAILABLE
    assert result.freshness.status is AvailabilityStatus.UNAVAILABLE
    assert result.confidence == 0
    assert result.market.performance.reason


def test_stale_daily_observations_are_reported() -> None:
    target, _ = make_service(AssetType.STOCK, age_days=10)

    result = asyncio.run(target.get_context("AAPL"))

    assert result.freshness.status is AvailabilityStatus.AVAILABLE
    assert result.freshness.state == "STALE"
    assert result.confidence < 80


def test_insufficient_common_dates_remove_relative_strength_and_reduce_confidence() -> None:
    complete, _ = make_service(AssetType.STOCK)
    insufficient, _ = make_service(AssetType.STOCK, reference_count=10)

    complete_result = asyncio.run(complete.get_context("AAPL"))
    result = asyncio.run(insufficient.get_context("AAPL"))

    comparison = result.relative_strength.versus_market
    assert comparison.status is AvailabilityStatus.UNAVAILABLE
    assert comparison.value is None
    assert comparison.alignment is not None
    assert comparison.alignment.actual_overlap_count == 10
    assert comparison.alignment.alignment_sufficient is False
    assert result.confidence < complete_result.confidence
    assert any("common daily observations" in warning for warning in result.warnings)
