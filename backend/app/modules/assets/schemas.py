from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field

from app.modules.intelligence.schemas import FreshnessMetadata, MarketState, VolatilityState


class AssetType(StrEnum):
    STOCK = "STOCK"
    GOLD = "GOLD"
    ETF = "ETF"
    UNKNOWN = "UNKNOWN"


class FundamentalCondition(StrEnum):
    STRONG = "STRONG"
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    WEAK = "WEAK"
    UNAVAILABLE = "UNAVAILABLE"


class AllocationItem(BaseModel):
    name: str
    weight_percentage: Decimal | None = None


class StockProfile(BaseModel):
    company_name: str | None = None
    country: str | None = None
    sector: str | None = None
    industry: str | None = None


class GoldProfile(BaseModel):
    commodity_category: str = "Precious metal"
    base_asset: str = "XAU"
    quote_currency: str = "USD"
    note: str = "Company fundamentals are not applicable to gold."


class EtfProfile(BaseModel):
    fund_name: str | None = None
    fund_provider: str | None = None
    fund_category: str | None = None
    inception_date: date | None = None


class StockMetrics(BaseModel):
    market_capitalization: Decimal | None = None
    pe_ratio: Decimal | None = None
    forward_pe_ratio: Decimal | None = None
    eps: Decimal | None = None
    revenue: Decimal | None = None
    revenue_growth_percentage: Decimal | None = None
    net_income: Decimal | None = None
    profit_margin_percentage: Decimal | None = None
    operating_margin_percentage: Decimal | None = None
    total_debt: Decimal | None = None
    total_cash: Decimal | None = None
    debt_to_equity: Decimal | None = None
    dividend_yield_percentage: Decimal | None = None
    high_52_week: Decimal | None = None
    low_52_week: Decimal | None = None
    average_volume: Decimal | None = None


class GoldMetrics(BaseModel):
    current_price: Decimal | None = None
    trading_status: MarketState = MarketState.UNKNOWN
    high_52_week: Decimal | None = None
    low_52_week: Decimal | None = None
    recent_volatility: VolatilityState | None = None
    technical_snapshot_reference: str | None = None


class EtfMetrics(BaseModel):
    expense_ratio_percentage: Decimal | None = None
    net_assets: Decimal | None = None
    holdings_count: int | None = None
    distribution_yield_percentage: Decimal | None = None
    high_52_week: Decimal | None = None
    low_52_week: Decimal | None = None
    average_volume: Decimal | None = None
    top_holdings: list[AllocationItem] | None = None
    sector_allocation: list[AllocationItem] | None = None
    geographic_allocation: list[AllocationItem] | None = None


class StockFundamentalClassification(BaseModel):
    methodology_version: str
    profitability: FundamentalCondition
    growth: FundamentalCondition
    debt: FundamentalCondition
    valuation: FundamentalCondition
    dividend: FundamentalCondition
    overall: FundamentalCondition


class AssetAvailability(BaseModel):
    classification: bool = True
    profile: bool = False
    metrics: bool = False
    fundamentals: bool = False
    holdings: bool = False
    allocations: bool = False
    technical_snapshot: bool = False


class AssetIntelligenceResponse(BaseModel):
    symbol: str
    display_name: str | None = None
    asset_type: AssetType
    exchange: str | None = None
    currency: str | None = None
    provider: str
    source_timestamp: datetime | None = None
    generated_at: datetime
    freshness: FreshnessMetadata | None = None
    profile: StockProfile | GoldProfile | EtfProfile | None = Field(default=None)
    metrics: StockMetrics | GoldMetrics | EtfMetrics | None = Field(default=None)
    classification: StockFundamentalClassification | None = None
    warnings: list[str] = Field(default_factory=list)
    availability: AssetAvailability


class AssetResolution(BaseModel):
    symbol: str
    provider_symbol: str
    display_name: str | None = None
    asset_type: AssetType
    exchange: str | None = None
    currency: str | None = None


class ProviderAssetData(BaseModel):
    resolution: AssetResolution
    stock_profile: StockProfile | None = None
    stock_metrics: StockMetrics | None = None
    etf_profile: EtfProfile | None = None
    etf_metrics: EtfMetrics | None = None
    gold_metrics: GoldMetrics | None = None
    source_timestamp: datetime | None = None
    warnings: list[str] = Field(default_factory=list)
