from decimal import Decimal

from app.modules.intelligence.schemas import IndicatorSet
from app.modules.market_data.schemas import Candle

ZERO = Decimal("0")
HUNDRED = Decimal("100")


def ema(values: list[Decimal], period: int) -> Decimal | None:
    if period <= 0 or len(values) < period:
        return None
    result = sum(values[:period]) / Decimal(period)
    multiplier = Decimal(2) / Decimal(period + 1)
    for value in values[period:]:
        result = ((value - result) * multiplier) + result
    return result


def rsi(values: list[Decimal], period: int = 14) -> Decimal | None:
    if len(values) <= period:
        return None
    changes = [current - previous for previous, current in zip(values, values[1:], strict=False)]
    gains = [max(change, ZERO) for change in changes]
    losses = [max(-change, ZERO) for change in changes]
    average_gain = sum(gains[:period]) / Decimal(period)
    average_loss = sum(losses[:period]) / Decimal(period)
    for gain, loss in zip(gains[period:], losses[period:], strict=True):
        average_gain = ((average_gain * Decimal(period - 1)) + gain) / Decimal(period)
        average_loss = ((average_loss * Decimal(period - 1)) + loss) / Decimal(period)
    if average_loss == ZERO:
        return HUNDRED
    strength = average_gain / average_loss
    return HUNDRED - (HUNDRED / (Decimal(1) + strength))


def atr(candles: list[Candle], period: int = 14) -> Decimal | None:
    if len(candles) <= period:
        return None
    ranges: list[Decimal] = []
    for previous, current in zip(candles, candles[1:], strict=False):
        ranges.append(
            max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close),
            )
        )
    result = sum(ranges[:period]) / Decimal(period)
    for value in ranges[period:]:
        result = ((result * Decimal(period - 1)) + value) / Decimal(period)
    return result


def calculate_indicators(candles: list[Candle]) -> IndicatorSet:
    ordered = sorted(candles, key=lambda candle: candle.time)
    closes = [candle.close for candle in ordered]
    volumes = [Decimal(candle.volume) for candle in ordered if candle.volume is not None]
    latest = ordered[-1] if ordered else None
    previous = ordered[-2] if len(ordered) >= 2 else None
    previous_close = previous.close if previous else None
    daily_change = (
        ((latest.close - previous_close) / previous_close) * HUNDRED
        if latest and previous_close and previous_close > ZERO
        else None
    )
    gap = (
        ((latest.open - previous_close) / previous_close) * HUNDRED
        if latest and previous_close and previous_close > ZERO
        else None
    )
    year = ordered[-252:] if ordered else []
    return IndicatorSet(
        ema20=ema(closes, 20),
        ema50=ema(closes, 50),
        rsi14=rsi(closes),
        atr14=atr(ordered),
        average_volume=(sum(volumes[-20:]) / Decimal(len(volumes[-20:]))) if volumes else None,
        high_52_week=max((candle.high for candle in year), default=None),
        low_52_week=min((candle.low for candle in year), default=None),
        daily_change_percentage=daily_change,
        previous_close=previous_close,
        gap_percentage=gap,
    )
