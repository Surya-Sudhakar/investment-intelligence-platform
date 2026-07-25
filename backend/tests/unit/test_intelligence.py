import asyncio
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal

from app.modules.intelligence.aggregation import CandleAggregator, bucket_start
from app.modules.intelligence.freshness import classify_freshness
from app.modules.intelligence.indicators import atr, ema, rsi
from app.modules.intelligence.market_status import ExchangeSchedule, determine_market_status
from app.modules.intelligence.polling import QuotePollingEngine
from app.modules.intelligence.schemas import (
    FreshnessState,
    IndicatorSet,
    MarketState,
    MomentumState,
    TrendState,
    VolatilityState,
)
from app.modules.intelligence.signals import (
    detect_momentum,
    detect_support_resistance,
    detect_trend,
    detect_volatility,
)
from app.modules.market_data.schemas import Candle, DataStatus, Interval, Quote

NOW = datetime(2026, 7, 24, 12, tzinfo=UTC)


def quote(price: str, at: datetime = NOW) -> Quote:
    return Quote(
        symbol="TEST",
        price=Decimal(price),
        timestamp=at,
        received_at=at,
        provider="test",
        delayed=False,
        data_status=DataStatus.UNKNOWN,
        age_seconds=0,
    )


def candle(index: int, close: Decimal) -> Candle:
    return Candle(
        symbol="TEST",
        interval=Interval.ONE_DAY,
        time=NOW + timedelta(days=index),
        open=close,
        high=close + 1,
        low=close - 1,
        close=close,
        volume=100 + index,
        is_complete=True,
        provider="test",
        source_timestamp=NOW + timedelta(days=index),
        received_at=NOW + timedelta(days=index),
        data_status=DataStatus.END_OF_DAY,
    )


def indicators(**updates: Decimal | None) -> IndicatorSet:
    values = {
        "ema20": Decimal("105"),
        "ema50": Decimal("100"),
        "rsi14": Decimal("60"),
        "atr14": Decimal("2"),
        "average_volume": None,
        "high_52_week": None,
        "low_52_week": None,
        "daily_change_percentage": None,
        "previous_close": None,
        "gap_percentage": None,
    }
    values.update(updates)
    return IndicatorSet(**values)


def test_freshness_states() -> None:
    result = classify_freshness(
        source_timestamp=NOW - timedelta(seconds=10),
        received_at=NOW,
        provider_delayed=False,
        market_status=MarketState.OPEN,
        provider_reachable=True,
        live_threshold_seconds=60,
        stale_threshold_seconds=900,
        evaluated_at=NOW,
    )
    assert result.state == FreshnessState.LIVE
    disconnected = classify_freshness(
        source_timestamp=NOW,
        received_at=NOW,
        provider_delayed=False,
        market_status=MarketState.OPEN,
        provider_reachable=False,
        live_threshold_seconds=60,
        stale_threshold_seconds=900,
        evaluated_at=NOW,
    )
    assert disconnected.state == FreshnessState.DISCONNECTED


def test_market_status_is_timezone_aware_and_handles_holidays() -> None:
    schedule = ExchangeSchedule("UTC", time(9), time(17), holidays=frozenset({NOW.date()}))
    assert determine_market_status(schedule, NOW).state == MarketState.HOLIDAY
    assert determine_market_status(None, NOW).state == MarketState.UNKNOWN


def test_indicators() -> None:
    values = [Decimal(index) for index in range(10, 70)]
    assert ema(values, 20) is not None
    assert rsi(values) == Decimal("100")
    assert atr([candle(index, value) for index, value in enumerate(values)]) == Decimal("2")


def test_classifiers_and_levels() -> None:
    current = indicators()
    assert detect_trend(Decimal("110"), current) == TrendState.STRONG_UPTREND
    assert detect_momentum(current) == MomentumState.BULLISH
    assert detect_volatility(Decimal("100"), current) == VolatilityState.NORMAL
    prices = [Decimal(value) for value in (100, 95, 102, 110, 103)]
    levels = detect_support_resistance(
        [candle(index, value) for index, value in enumerate(prices)], Decimal("103")
    )
    assert levels.nearest_support == Decimal("94")
    assert levels.nearest_resistance == Decimal("111")


def test_aggregation_alignment_duplicates_and_out_of_order() -> None:
    aggregator = CandleAggregator()
    later = quote("12", NOW + timedelta(minutes=4))
    earlier = quote("10", NOW + timedelta(minutes=1))
    aggregator.add(later, Interval.FIVE_MINUTES)
    result = aggregator.add(earlier, Interval.FIVE_MINUTES)
    aggregator.add(earlier, Interval.FIVE_MINUTES)
    assert bucket_start(earlier.timestamp, Interval.FIVE_MINUTES).minute % 5 == 0
    assert result.open == Decimal("12")
    assert result.close == Decimal("12")
    assert result.low == Decimal("10")
    aggregator.finalize_before(NOW + timedelta(minutes=10))
    assert aggregator.candles("TEST", Interval.FIVE_MINUTES)[0].is_complete


def test_polling_avoids_duplicates_and_stops() -> None:
    async def scenario() -> None:
        calls = 0

        async def fetch(_: str) -> Quote:
            nonlocal calls
            calls += 1
            return quote("10")

        engine = QuotePollingEngine(fetch, 0.01)
        assert engine.start("test")
        assert not engine.start("TEST")
        await asyncio.sleep(0.03)
        assert calls >= 1
        assert await engine.stop("TEST")
        assert engine.active_count == 0

    asyncio.run(scenario())
