from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, time
from decimal import ROUND_HALF_UP, Decimal

from app.modules.market_context.config import OVERALL_THRESHOLDS, PERFORMANCE_THRESHOLDS
from app.modules.market_context.schemas import (
    AlignmentMetadata,
    ContextClassification,
    ContextReference,
    PerformanceObservation,
    RelativeStrengthObservation,
)
from app.modules.market_data.schemas import Candle

SIGNALS = {
    ContextClassification.VERY_STRONG: 3,
    ContextClassification.STRONG: 2,
    ContextClassification.POSITIVE: 1,
    ContextClassification.NEUTRAL: 0,
    ContextClassification.WEAK: -1,
    ContextClassification.VERY_WEAK: -3,
}


def classify_performance(value: Decimal) -> ContextClassification:
    number = float(value)
    if number >= PERFORMANCE_THRESHOLDS["very_strong"]:
        return ContextClassification.VERY_STRONG
    if number >= PERFORMANCE_THRESHOLDS["strong"]:
        return ContextClassification.STRONG
    if number >= PERFORMANCE_THRESHOLDS["positive"]:
        return ContextClassification.POSITIVE
    if number > PERFORMANCE_THRESHOLDS["neutral"]:
        return ContextClassification.NEUTRAL
    if number > PERFORMANCE_THRESHOLDS["weak"]:
        return ContextClassification.WEAK
    return ContextClassification.VERY_WEAK


def classify_overall(value: float) -> ContextClassification:
    if value >= OVERALL_THRESHOLDS["very_strong"]:
        return ContextClassification.VERY_STRONG
    if value >= OVERALL_THRESHOLDS["strong"]:
        return ContextClassification.STRONG
    if value >= OVERALL_THRESHOLDS["positive"]:
        return ContextClassification.POSITIVE
    if value > OVERALL_THRESHOLDS["neutral"]:
        return ContextClassification.NEUTRAL
    if value > OVERALL_THRESHOLDS["weak"]:
        return ContextClassification.WEAK
    return ContextClassification.VERY_WEAK


def performance(
    reference: ContextReference,
    candles: Sequence[Candle],
    lookback_sessions: int,
    minimum_sessions: int,
) -> PerformanceObservation | None:
    usable = sorted((item for item in candles if item.is_complete), key=lambda item: item.time)
    usable = usable[-lookback_sessions:]
    if len(usable) < minimum_sessions:
        return None
    change = ((usable[-1].close / usable[0].close) - Decimal(1)) * Decimal(100)
    rounded = change.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return PerformanceObservation(
        reference=reference,
        return_percentage=rounded,
        classification=classify_performance(rounded),
        observations=len(usable),
        first_timestamp=usable[0].source_timestamp,
        last_timestamp=usable[-1].source_timestamp,
    )


def relative_strength(
    asset_symbol: str,
    asset: PerformanceObservation,
    reference: PerformanceObservation,
) -> RelativeStrengthObservation:
    difference = (asset.return_percentage - reference.return_percentage).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return RelativeStrengthObservation(
        asset_symbol=asset_symbol,
        reference=reference.reference,
        difference_percentage_points=difference,
        classification=classify_performance(difference),
        overlapping_observations=min(asset.observations, reference.observations),
    )


def canonical_daily_date(candle: Candle) -> date:
    return candle.time.astimezone(UTC).date()


def _daily_close_map(candles: Sequence[Candle]) -> dict[date, Candle]:
    usable = [item for item in candles if item.is_complete]
    ordered = sorted(
        usable,
        key=lambda item: (
            canonical_daily_date(item),
            item.source_timestamp,
            item.received_at,
            item.time,
            item.close,
        ),
    )
    return {canonical_daily_date(item): item for item in ordered}


def aligned_relative_strength(
    asset_symbol: str,
    asset_reference: ContextReference,
    asset_candles: Sequence[Candle],
    reference: ContextReference,
    reference_candles: Sequence[Candle],
    requested_lookback: int,
    minimum_required: int,
) -> tuple[RelativeStrengthObservation | None, AlignmentMetadata]:
    asset_by_date = _daily_close_map(asset_candles)
    reference_by_date = _daily_close_map(reference_candles)
    shared_dates = sorted(set(asset_by_date).intersection(reference_by_date))
    aligned_dates = shared_dates[-requested_lookback:]
    sufficient = len(aligned_dates) >= minimum_required
    start = datetime.combine(aligned_dates[0], time.min, tzinfo=UTC) if aligned_dates else None
    end = datetime.combine(aligned_dates[-1], time.min, tzinfo=UTC) if aligned_dates else None
    metadata = AlignmentMetadata(
        actual_overlap_count=len(aligned_dates),
        aligned_start_timestamp=start,
        aligned_end_timestamp=end,
        requested_lookback=requested_lookback,
        minimum_required=minimum_required,
        alignment_sufficient=sufficient,
    )
    if not sufficient:
        return None, metadata

    asset_selected = [asset_by_date[item] for item in aligned_dates]
    reference_selected = [reference_by_date[item] for item in aligned_dates]
    asset_performance = performance(
        asset_reference,
        asset_selected,
        requested_lookback,
        minimum_required,
    )
    reference_performance = performance(
        reference,
        reference_selected,
        requested_lookback,
        minimum_required,
    )
    if asset_performance is None or reference_performance is None:
        return None, metadata.model_copy(update={"alignment_sufficient": False})
    return relative_strength(asset_symbol, asset_performance, reference_performance), metadata


def weighted_context(
    components: Mapping[str, ContextClassification],
    weights: Mapping[str, int],
) -> tuple[ContextClassification | None, float]:
    available_weight = sum(weights[name] for name in components)
    if not available_weight:
        return None, 0.0
    score = sum(SIGNALS[value] * weights[name] for name, value in components.items())
    return classify_overall(score / available_weight), available_weight / sum(weights.values())


def source_range(
    observations: Sequence[PerformanceObservation],
) -> tuple[datetime | None, datetime | None]:
    if not observations:
        return None, None
    return (
        min(item.first_timestamp for item in observations),
        max(item.last_timestamp for item in observations),
    )
