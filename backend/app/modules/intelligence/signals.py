from decimal import Decimal

from app.modules.intelligence.schemas import (
    IndicatorSet,
    MomentumState,
    SupportResistance,
    TrendState,
    VolatilityState,
)
from app.modules.market_data.schemas import Candle

HUNDRED = Decimal("100")


def detect_trend(price: Decimal, indicators: IndicatorSet) -> TrendState:
    if indicators.ema20 is None or indicators.ema50 is None or indicators.ema50 == 0:
        return TrendState.UNKNOWN
    spread = ((indicators.ema20 - indicators.ema50) / indicators.ema50) * HUNDRED
    if price > indicators.ema20 > indicators.ema50:
        return TrendState.STRONG_UPTREND if spread >= Decimal("2") else TrendState.UPTREND
    if price < indicators.ema20 < indicators.ema50:
        return TrendState.STRONG_DOWNTREND if spread <= Decimal("-2") else TrendState.DOWNTREND
    return TrendState.SIDEWAYS


def detect_momentum(indicators: IndicatorSet) -> MomentumState:
    if indicators.rsi14 is None or indicators.ema20 is None or indicators.ema50 is None:
        return MomentumState.UNKNOWN
    bullish = indicators.ema20 > indicators.ema50
    if indicators.rsi14 >= 70 and bullish:
        return MomentumState.STRONG_BULLISH
    if indicators.rsi14 > 55 and bullish:
        return MomentumState.BULLISH
    if indicators.rsi14 <= 30 and not bullish:
        return MomentumState.STRONG_BEARISH
    if indicators.rsi14 < 45 and not bullish:
        return MomentumState.BEARISH
    return MomentumState.NEUTRAL


def detect_volatility(price: Decimal, indicators: IndicatorSet) -> VolatilityState:
    if indicators.atr14 is None or price <= 0:
        return VolatilityState.UNKNOWN
    percentage = indicators.atr14 / price * HUNDRED
    if percentage < Decimal("0.5"):
        return VolatilityState.VERY_LOW
    if percentage < Decimal("1"):
        return VolatilityState.LOW
    if percentage < Decimal("2.5"):
        return VolatilityState.NORMAL
    if percentage < Decimal("5"):
        return VolatilityState.HIGH
    return VolatilityState.EXTREME


def detect_support_resistance(candles: list[Candle], price: Decimal) -> SupportResistance:
    ordered = sorted(candles, key=lambda candle: candle.time)
    supports: list[Decimal] = []
    resistances: list[Decimal] = []
    for index in range(1, len(ordered) - 1):
        previous, current, following = ordered[index - 1 : index + 2]
        if current.low <= previous.low and current.low <= following.low:
            supports.append(current.low)
        if current.high >= previous.high and current.high >= following.high:
            resistances.append(current.high)
    support = max((level for level in supports if level <= price), default=None)
    resistance = min((level for level in resistances if level >= price), default=None)
    support_distance = ((price - support) / price * HUNDRED) if support and price > 0 else None
    resistance_distance = (
        ((resistance - price) / price * HUNDRED) if resistance and price > 0 else None
    )
    distances = [value for value in (support_distance, resistance_distance) if value is not None]
    return SupportResistance(
        nearest_support=support,
        nearest_resistance=resistance,
        distance_to_support_percentage=support_distance,
        distance_to_resistance_percentage=resistance_distance,
        breakout_risk=min(distances) <= Decimal("0.5") if distances else None,
    )
