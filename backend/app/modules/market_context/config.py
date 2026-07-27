from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class MarketContextConfig:
    methodology_version: str = "market-context-v1"
    lookback_sessions: int = 20
    requested_candles: int = 30
    minimum_sessions: int = 15
    current_max_age_days: int = 4
    stale_age_days: int = 8


CONTEXT_CONFIG = MarketContextConfig()

PERFORMANCE_THRESHOLDS = MappingProxyType(
    {
        "very_strong": 5.0,
        "strong": 2.5,
        "positive": 0.5,
        "neutral": -0.5,
        "weak": -2.5,
    }
)

OVERALL_THRESHOLDS = MappingProxyType(
    {
        "very_strong": 2.25,
        "strong": 1.25,
        "positive": 0.35,
        "neutral": -0.35,
        "weak": -1.25,
    }
)

STOCK_WEIGHTS = MappingProxyType(
    {
        "market_trend": 15,
        "sector_trend": 20,
        "industry_trend": 15,
        "asset_vs_market": 20,
        "asset_vs_sector": 20,
        "asset_vs_industry": 10,
    }
)
GOLD_WEIGHTS = MappingProxyType(
    {
        "gold_trend": 35,
        "silver_trend": 20,
        "gold_vs_silver": 20,
        "commodity_index_trend": 15,
        "commodity_alignment": 10,
    }
)
ETF_WEIGHTS = MappingProxyType(
    {"benchmark_trend": 35, "etf_vs_benchmark": 50, "fund_category_trend": 15}
)

SECTOR_PROXIES = MappingProxyType(
    {
        "communication services": ("XLC", "Communication Services Select Sector SPDR Fund"),
        "consumer discretionary": ("XLY", "Consumer Discretionary Select Sector SPDR Fund"),
        "consumer staples": ("XLP", "Consumer Staples Select Sector SPDR Fund"),
        "energy": ("XLE", "Energy Select Sector SPDR Fund"),
        "financials": ("XLF", "Financial Select Sector SPDR Fund"),
        "health care": ("XLV", "Health Care Select Sector SPDR Fund"),
        "healthcare": ("XLV", "Health Care Select Sector SPDR Fund"),
        "industrials": ("XLI", "Industrial Select Sector SPDR Fund"),
        "information technology": ("XLK", "Technology Select Sector SPDR Fund"),
        "technology": ("XLK", "Technology Select Sector SPDR Fund"),
        "materials": ("XLB", "Materials Select Sector SPDR Fund"),
        "real estate": ("XLRE", "Real Estate Select Sector SPDR Fund"),
        "utilities": ("XLU", "Utilities Select Sector SPDR Fund"),
    }
)
