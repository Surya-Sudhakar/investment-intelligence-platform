from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.modules.intelligence.schemas import FreshnessState, MarketState
from app.modules.market_data.schemas import DataStatus, Interval


class TechnicalAssessmentState(StrEnum):
    STRONGLY_BULLISH = "STRONGLY_BULLISH"
    BULLISH = "BULLISH"
    NEUTRAL = "NEUTRAL"
    BEARISH = "BEARISH"
    STRONGLY_BEARISH = "STRONGLY_BEARISH"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    EXTREME = "EXTREME"


class TimeHorizon(StrEnum):
    SWING_POSITION = "SWING_POSITION"


class AssessmentFactor(BaseModel):
    code: str
    message: str


class ComponentScore(BaseModel):
    name: str
    weight: int
    available: bool
    raw_value: str | float | None
    signal: float | None = Field(ge=-1, le=1)
    weighted_contribution: float | None
    explanation: str


class RiskComponent(BaseModel):
    name: str
    weight: int
    available: bool
    raw_value: str | float | None
    risk_value: float | None = Field(ge=0, le=100)
    weighted_contribution: float | None
    explanation: str


class RiskAssessment(BaseModel):
    score: int = Field(ge=0, le=100)
    level: RiskLevel
    data_coverage_percentage: float = Field(ge=0, le=100)
    components: list[RiskComponent]


class DataQualityInformation(BaseModel):
    freshness_state: FreshnessState
    source_age_seconds: int | None
    quote_data_status: DataStatus
    quote_cached: bool
    market_status: MarketState
    available_directional_weight: int
    eligible_directional_weight: int
    input_coverage_percentage: float = Field(ge=0, le=100)
    issues: list[str]


class TechnicalAssessment(BaseModel):
    symbol: str
    interval: Interval
    time_horizon: TimeHorizon
    assessment: TechnicalAssessmentState
    technical_score: int = Field(ge=0, le=100)
    confidence_score: int = Field(ge=0, le=100)
    risk: RiskAssessment
    components: list[ComponentScore]
    supporting_factors: list[AssessmentFactor]
    conflicting_factors: list[AssessmentFactor]
    risk_factors: list[AssessmentFactor]
    missing_data_factors: list[AssessmentFactor]
    data_quality: DataQualityInformation
    scoring_version: str
    snapshot_timestamp: datetime
    generated_at: datetime


class AssessmentHealth(BaseModel):
    status: str
    scoring_version: str
    intelligence_ready: bool
    checked_at: datetime
    message: str
