from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.modules.market_context.calculation import (
    aligned_relative_strength,
    classify_overall,
    classify_performance,
    performance,
    relative_strength,
    weighted_context,
)
from app.modules.market_context.schemas import (
    ContextClassification,
    ContextReference,
    ReferenceKind,
)
from app.modules.market_data.schemas import Candle, DataStatus, Interval


def candles(start: Decimal, step: Decimal, count: int = 20) -> list[Candle]:
    now = datetime.now(UTC) - timedelta(days=count)
    output = []
    for index in range(count):
        price = start + step * index
        timestamp = now + timedelta(days=index)
        output.append(
            Candle(
                symbol="TEST",
                interval=Interval.ONE_DAY,
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
    return output


def reference(symbol: str) -> ContextReference:
    return ContextReference(symbol=symbol, name=symbol, kind=ReferenceKind.MARKET_PROXY)


def aligned(
    asset_candles: list[Candle],
    reference_candles: list[Candle],
    lookback: int = 20,
    minimum: int = 15,
):
    return aligned_relative_strength(
        "AAPL",
        reference("AAPL"),
        asset_candles,
        reference("SPY"),
        reference_candles,
        lookback,
        minimum,
    )


def test_performance_thresholds_are_deterministic() -> None:
    assert classify_performance(Decimal("5")) is ContextClassification.VERY_STRONG
    assert classify_performance(Decimal("2.5")) is ContextClassification.STRONG
    assert classify_performance(Decimal("0.5")) is ContextClassification.POSITIVE
    assert classify_performance(Decimal("0")) is ContextClassification.NEUTRAL
    assert classify_performance(Decimal("-0.5")) is ContextClassification.WEAK
    assert classify_performance(Decimal("-2.5")) is ContextClassification.VERY_WEAK
    assert classify_overall(2.25) is ContextClassification.VERY_STRONG


def test_performance_and_relative_strength_use_observed_values() -> None:
    asset = performance(reference("AAPL"), candles(Decimal("100"), Decimal("1")), 20, 15)
    market = performance(reference("SPY"), candles(Decimal("100"), Decimal("0.2")), 20, 15)

    assert asset is not None
    assert market is not None
    comparison = relative_strength("AAPL", asset, market)
    assert comparison.difference_percentage_points > 0
    assert comparison.classification in {
        ContextClassification.STRONG,
        ContextClassification.VERY_STRONG,
    }


def test_missing_components_reduce_coverage_without_becoming_neutral() -> None:
    context, coverage = weighted_context(
        {"market_trend": ContextClassification.POSITIVE},
        {"market_trend": 20, "sector_trend": 80},
    )
    assert context is ContextClassification.POSITIVE
    assert coverage == 0.2

    no_context, no_coverage = weighted_context(
        {},
        {"market_trend": 100},
    )
    assert no_context is None
    assert no_coverage == 0


def test_insufficient_observations_do_not_invent_performance() -> None:
    assert performance(reference("AAPL"), candles(Decimal("100"), Decimal("1"), 10), 20, 15) is None


def test_alignment_with_identical_calendars_uses_common_window() -> None:
    result, metadata = aligned(
        candles(Decimal("100"), Decimal("1")),
        candles(Decimal("100"), Decimal("0.5")),
    )
    assert result is not None
    assert metadata.actual_overlap_count == 20
    assert metadata.alignment_sufficient is True
    assert metadata.aligned_start_timestamp is not None
    assert metadata.aligned_end_timestamp is not None
    assert result.overlapping_observations == 20


def test_alignment_handles_one_missing_trading_day() -> None:
    asset = candles(Decimal("100"), Decimal("1"))
    market = candles(Decimal("100"), Decimal("0.5"))
    market.pop(8)
    result, metadata = aligned(asset, market)
    assert result is not None
    assert metadata.actual_overlap_count == 19
    assert result.overlapping_observations == 19


def test_alignment_handles_multiple_missing_and_holiday_sessions() -> None:
    asset = candles(Decimal("100"), Decimal("1"))
    market = candles(Decimal("100"), Decimal("0.5"))
    market = [item for index, item in enumerate(market) if index not in {4, 5, 10, 11}]
    result, metadata = aligned(asset, market)
    assert result is not None
    assert metadata.actual_overlap_count == 16
    assert metadata.alignment_sufficient is True


def test_delayed_reference_and_different_latest_date_share_the_same_end() -> None:
    asset = candles(Decimal("100"), Decimal("1"), 22)
    market = [
        item.model_copy(
            update={
                "time": item.time - timedelta(days=2),
                "source_timestamp": item.source_timestamp - timedelta(days=2),
            }
        )
        for item in candles(Decimal("100"), Decimal("0.5"), 20)
    ]
    result, metadata = aligned(asset, market)
    assert result is not None
    assert metadata.actual_overlap_count == 20
    assert metadata.aligned_end_timestamp is not None
    assert metadata.aligned_end_timestamp.date() == market[-1].time.date()
    assert metadata.aligned_end_timestamp.date() != asset[-1].time.date()


def test_no_common_dates_returns_insufficient_alignment() -> None:
    asset = candles(Decimal("100"), Decimal("1"))
    market = candles(Decimal("100"), Decimal("0.5"))
    shifted = [
        item.model_copy(
            update={
                "time": item.time + timedelta(days=100),
                "source_timestamp": item.source_timestamp + timedelta(days=100),
            }
        )
        for item in market
    ]
    result, metadata = aligned(asset, shifted)
    assert result is None
    assert metadata.actual_overlap_count == 0
    assert metadata.alignment_sufficient is False
    assert metadata.aligned_start_timestamp is None
    assert metadata.aligned_end_timestamp is None


def test_insufficient_overlap_returns_no_relative_strength() -> None:
    result, metadata = aligned(
        candles(Decimal("100"), Decimal("1")),
        candles(Decimal("100"), Decimal("0.5"), 14),
    )
    assert result is None
    assert metadata.actual_overlap_count == 14
    assert metadata.requested_lookback == 20
    assert metadata.minimum_required == 15
    assert metadata.alignment_sufficient is False


def test_unordered_observations_are_aligned_chronologically() -> None:
    asset = list(reversed(candles(Decimal("100"), Decimal("1"))))
    market = candles(Decimal("100"), Decimal("0.5"))
    market = market[::2] + market[1::2]
    result, metadata = aligned(asset, market)
    assert result is not None
    assert metadata.aligned_start_timestamp is not None
    assert metadata.aligned_end_timestamp is not None
    assert metadata.aligned_start_timestamp < metadata.aligned_end_timestamp
    assert result.overlapping_observations == 20


def test_duplicate_dates_are_deduplicated_deterministically() -> None:
    asset = candles(Decimal("100"), Decimal("1"))
    duplicate = asset[5].model_copy(
        update={"received_at": asset[5].received_at + timedelta(seconds=1)}
    )
    market = candles(Decimal("100"), Decimal("0.5"))
    first, first_metadata = aligned([*asset, duplicate], market)
    second, second_metadata = aligned([duplicate, *reversed(asset)], market)
    assert first == second
    assert first_metadata == second_metadata
    assert first_metadata.actual_overlap_count == 20


def test_alignment_is_deterministic_after_lookback_truncation() -> None:
    asset = candles(Decimal("100"), Decimal("1"), 25)
    market = candles(Decimal("100"), Decimal("0.5"), 25)
    first, first_metadata = aligned(asset, market)
    second, second_metadata = aligned(list(reversed(asset)), list(reversed(market)))
    assert first == second
    assert first_metadata == second_metadata
    assert first_metadata.actual_overlap_count == 20
