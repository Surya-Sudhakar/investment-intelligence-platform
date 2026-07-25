from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel

from app.modules.market_data.schemas import Quote


class FreshnessState(StrEnum):
    LIVE = "LIVE"
    DELAYED = "DELAYED"
    STALE = "STALE"
    MARKET_CLOSED = "MARKET_CLOSED"
    DISCONNECTED = "DISCONNECTED"
    FALLBACK = "FALLBACK"
    UNKNOWN = "UNKNOWN"


class MarketState(StrEnum):
    OPEN = "OPEN"
    PRE_MARKET = "PRE_MARKET"
    AFTER_HOURS = "AFTER_HOURS"
    CLOSED = "CLOSED"
    HOLIDAY = "HOLIDAY"
    UNKNOWN = "UNKNOWN"


class TrendState(StrEnum):
    STRONG_UPTREND = "STRONG_UPTREND"
    UPTREND = "UPTREND"
    SIDEWAYS = "SIDEWAYS"
    DOWNTREND = "DOWNTREND"
    STRONG_DOWNTREND = "STRONG_DOWNTREND"
    UNKNOWN = "UNKNOWN"


class MomentumState(StrEnum):
    STRONG_BULLISH = "STRONG_BULLISH"
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    STRONG_BEARISH = "STRONG_BEARISH"
    UNKNOWN = "UNKNOWN"


class VolatilityState(StrEnum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    EXTREME = "EXTREME"
    UNKNOWN = "UNKNOWN"


class FreshnessMetadata(BaseModel):
    state: FreshnessState
    age_seconds: int | None
    threshold_seconds: int
    source_timestamp: datetime | None
    evaluated_at: datetime
    reason: str


class MarketStatusResult(BaseModel):
    state: MarketState
    exchange_timezone: str | None
    evaluated_at: datetime
    next_transition_at: datetime | None = None
    reason: str


class IndicatorSet(BaseModel):
    ema20: Decimal | None
    ema50: Decimal | None
    rsi14: Decimal | None
    atr14: Decimal | None
    average_volume: Decimal | None
    high_52_week: Decimal | None
    low_52_week: Decimal | None
    daily_change_percentage: Decimal | None
    previous_close: Decimal | None
    gap_percentage: Decimal | None


class SupportResistance(BaseModel):
    nearest_support: Decimal | None
    nearest_resistance: Decimal | None
    distance_to_support_percentage: Decimal | None
    distance_to_resistance_percentage: Decimal | None
    breakout_risk: bool | None


class IntelligenceSnapshot(BaseModel):
    symbol: str
    quote: Quote
    freshness: FreshnessMetadata
    market_status: MarketStatusResult
    trend: TrendState
    momentum: MomentumState
    volatility: VolatilityState
    indicators: IndicatorSet
    support_resistance: SupportResistance
    provider: str
    timestamp: datetime


class IntelligenceHealth(BaseModel):
    status: str
    market_data_configured: bool
    provider_reachable: bool
    polling_jobs: int
    checked_at: datetime
    message: str
