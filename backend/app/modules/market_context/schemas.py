from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from app.modules.assets.schemas import AssetType
from app.modules.market_data.schemas import Interval
from app.schemas.metadata import (
    AlignmentMetadata as AlignmentMetadata,
)
from app.schemas.metadata import (
    AvailabilityStatus as AvailabilityStatus,
)
from app.schemas.metadata import (
    AvailableValue as AvailableValue,
)
from app.schemas.metadata import (
    PartialDataStatus as PartialDataStatus,
)


class ContextClassification(StrEnum):
    VERY_STRONG = "VERY_STRONG"
    STRONG = "STRONG"
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    WEAK = "WEAK"
    VERY_WEAK = "VERY_WEAK"


class ReferenceKind(StrEnum):
    ASSET = "ASSET"
    INDEX = "INDEX"
    ETF_BENCHMARK = "ETF_BENCHMARK"
    MARKET_PROXY = "MARKET_PROXY"
    SECTOR_PROXY = "SECTOR_PROXY"
    INDUSTRY_PROXY = "INDUSTRY_PROXY"
    COMMODITY = "COMMODITY"
    COMMODITY_INDEX = "COMMODITY_INDEX"


class ContextReference(BaseModel):
    symbol: str
    name: str
    kind: ReferenceKind
    is_proxy: bool = False


class PerformanceObservation(BaseModel):
    reference: ContextReference
    return_percentage: Decimal
    classification: ContextClassification
    observations: int
    first_timestamp: datetime
    last_timestamp: datetime


class RelativeStrengthObservation(BaseModel):
    asset_symbol: str
    reference: ContextReference
    difference_percentage_points: Decimal
    classification: ContextClassification
    overlapping_observations: int


class ContextHorizon(BaseModel):
    interval: Interval = Interval.ONE_DAY
    lookback_sessions: int


class ContextFreshness(BaseModel):
    status: AvailabilityStatus
    state: str | None = None
    oldest_source_timestamp: datetime | None = None
    newest_source_timestamp: datetime | None = None
    age_days: int | None = Field(default=None, ge=0)
    reason: str


class MarketSection(BaseModel):
    primary_exchange: AvailableValue[str]
    primary_market_index: AvailableValue[ContextReference]
    reference: AvailableValue[ContextReference]
    performance: AvailableValue[PerformanceObservation]


class SectorSection(BaseModel):
    name: AvailableValue[str]
    reference: AvailableValue[ContextReference]
    performance: AvailableValue[PerformanceObservation]
    trend: AvailableValue[ContextClassification]


class IndustrySection(BaseModel):
    name: AvailableValue[str]
    reference: AvailableValue[ContextReference]
    performance: AvailableValue[PerformanceObservation]
    trend: AvailableValue[ContextClassification]


class CommoditySection(BaseModel):
    precious_metals_trend: AvailableValue[ContextClassification]
    silver_comparison: AvailableValue[RelativeStrengthObservation]
    commodity_index_trend: AvailableValue[ContextClassification]
    safe_haven_demand_trend: AvailableValue[ContextClassification]
    commodity_market_alignment: AvailableValue[ContextClassification]


class EtfSection(BaseModel):
    etf_category: AvailableValue[str]
    fund_category: AvailableValue[str]
    benchmark_index: AvailableValue[ContextReference]
    regional_exposure: AvailableValue[list[str]]
    sector_concentration: AvailableValue[list[str]]
    relative_performance: AvailableValue[RelativeStrengthObservation]


class RelativeStrengthSection(BaseModel):
    versus_market: AvailableValue[RelativeStrengthObservation]
    versus_sector: AvailableValue[RelativeStrengthObservation]
    versus_industry: AvailableValue[RelativeStrengthObservation]


class MarketContextAvailability(BaseModel):
    asset_performance: AvailabilityStatus
    market: AvailabilityStatus
    sector: AvailabilityStatus
    industry: AvailabilityStatus
    relative_strength: AvailabilityStatus
    commodity: AvailabilityStatus
    etf: AvailabilityStatus


class MarketContextResponse(BaseModel):
    symbol: str
    display_name: str
    asset_type: AssetType
    provider: str
    methodology_version: str
    horizon: ContextHorizon
    overall_context: AvailableValue[ContextClassification]
    confidence: int = Field(ge=0, le=100)
    partial_data_status: PartialDataStatus
    market: MarketSection
    sector: SectorSection
    industry: IndustrySection
    commodity: CommoditySection
    etf: EtfSection
    relative_strength: RelativeStrengthSection
    supporting_observations: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    freshness: ContextFreshness
    availability: MarketContextAvailability
    source_timestamp: AvailableValue[datetime]
    generated_at: datetime


class ContextReferences(BaseModel):
    market: ContextReference | None = None
    sector: ContextReference | None = None
    industry: ContextReference | None = None
    benchmark: ContextReference | None = None
    silver: ContextReference | None = None
    commodity_index: ContextReference | None = None
