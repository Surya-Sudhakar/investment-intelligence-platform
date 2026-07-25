from datetime import UTC, datetime

from app.modules.intelligence.schemas import (
    FreshnessMetadata,
    FreshnessState,
    MarketState,
)


def classify_freshness(
    *,
    source_timestamp: datetime | None,
    received_at: datetime,
    provider_delayed: bool,
    market_status: MarketState,
    provider_reachable: bool,
    live_threshold_seconds: int,
    stale_threshold_seconds: int,
    evaluated_at: datetime | None = None,
    fallback: bool = False,
) -> FreshnessMetadata:
    now = evaluated_at or datetime.now(UTC)
    if not provider_reachable:
        return FreshnessMetadata(
            state=FreshnessState.DISCONNECTED,
            age_seconds=None,
            threshold_seconds=stale_threshold_seconds,
            source_timestamp=source_timestamp,
            evaluated_at=now,
            reason="Market-data provider is not reachable.",
        )
    if fallback:
        state = FreshnessState.FALLBACK
        reason = "Fallback data source was used."
    elif source_timestamp is None:
        state = FreshnessState.UNKNOWN
        reason = "Provider source timestamp is unavailable."
    else:
        age = max(0, int((now - source_timestamp.astimezone(UTC)).total_seconds()))
        if market_status in {MarketState.CLOSED, MarketState.HOLIDAY}:
            state = FreshnessState.MARKET_CLOSED
            reason = "The configured exchange is closed."
        elif provider_delayed:
            state = FreshnessState.DELAYED
            reason = "The provider marks this data as delayed or end-of-day."
        elif age <= live_threshold_seconds:
            state = FreshnessState.LIVE
            reason = "Source timestamp is within the configured live threshold."
        elif age > stale_threshold_seconds:
            state = FreshnessState.STALE
            reason = "Source timestamp exceeds the configured stale threshold."
        else:
            state = FreshnessState.DELAYED
            reason = "Source timestamp exceeds the live threshold."
        return FreshnessMetadata(
            state=state,
            age_seconds=age,
            threshold_seconds=stale_threshold_seconds,
            source_timestamp=source_timestamp,
            evaluated_at=now,
            reason=reason,
        )
    return FreshnessMetadata(
        state=state,
        age_seconds=max(0, int((now - received_at.astimezone(UTC)).total_seconds())),
        threshold_seconds=stale_threshold_seconds,
        source_timestamp=source_timestamp,
        evaluated_at=now,
        reason=reason,
    )
