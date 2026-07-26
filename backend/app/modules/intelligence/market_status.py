from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.modules.intelligence.schemas import MarketState, MarketStatusResult


@dataclass(frozen=True)
class ExchangeSchedule:
    timezone: str
    open_time: time
    close_time: time
    pre_market_start: time | None = None
    after_hours_end: time | None = None
    holidays: frozenset[date] = frozenset()
    trading_weekdays: frozenset[int] = frozenset({0, 1, 2, 3, 4})


def determine_market_status(
    schedule: ExchangeSchedule | None, evaluated_at: datetime | None = None
) -> MarketStatusResult:
    now = evaluated_at or datetime.now(UTC)
    if schedule is None:
        return MarketStatusResult(
            state=MarketState.UNKNOWN,
            exchange_timezone=None,
            evaluated_at=now,
            reason="No exchange schedule is configured for this symbol.",
        )
    try:
        timezone = ZoneInfo(schedule.timezone)
    except ZoneInfoNotFoundError:
        return MarketStatusResult(
            state=MarketState.UNKNOWN,
            exchange_timezone=schedule.timezone,
            evaluated_at=now,
            reason="The configured exchange timezone is invalid.",
        )
    local = now.astimezone(timezone)
    if local.date() in schedule.holidays:
        state = MarketState.HOLIDAY
        reason = "The date is configured as an exchange holiday."
    elif local.weekday() not in schedule.trading_weekdays:
        state = MarketState.CLOSED
        reason = "The date is outside configured trading weekdays."
    elif (
        schedule.pre_market_start and schedule.pre_market_start <= local.time() < schedule.open_time
    ):
        state = MarketState.PRE_MARKET
        reason = "Current time is within the configured pre-market session."
    elif schedule.open_time <= local.time() < schedule.close_time:
        state = MarketState.OPEN
        reason = "Current time is within configured regular trading hours."
    elif (
        schedule.after_hours_end and schedule.close_time <= local.time() < schedule.after_hours_end
    ):
        state = MarketState.AFTER_HOURS
        reason = "Current time is within the configured after-hours session."
    else:
        state = MarketState.CLOSED
        reason = "Current time is outside configured trading sessions."
    return MarketStatusResult(
        state=state,
        exchange_timezone=schedule.timezone,
        evaluated_at=now,
        reason=reason,
    )
