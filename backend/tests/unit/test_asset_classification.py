from decimal import Decimal

from app.modules.assets.classification import classify_fundamentals
from app.modules.assets.schemas import FundamentalCondition, StockMetrics


def test_classifies_complete_strong_fundamentals() -> None:
    result = classify_fundamentals(
        StockMetrics(
            profit_margin_percentage=Decimal("25"),
            operating_margin_percentage=Decimal("20"),
            revenue_growth_percentage=Decimal("18"),
            debt_to_equity=Decimal("40"),
            pe_ratio=Decimal("14"),
            dividend_yield_percentage=Decimal("4"),
        )
    )

    assert result.methodology_version == "fundamentals-v1"
    assert result.profitability is FundamentalCondition.STRONG
    assert result.overall is FundamentalCondition.STRONG


def test_missing_metrics_are_not_invented() -> None:
    result = classify_fundamentals(StockMetrics(pe_ratio=Decimal("20")))

    assert result.profitability is FundamentalCondition.UNAVAILABLE
    assert result.growth is FundamentalCondition.UNAVAILABLE
    assert result.debt is FundamentalCondition.UNAVAILABLE
    assert result.overall is FundamentalCondition.UNAVAILABLE


def test_zero_dividend_is_neutral() -> None:
    result = classify_fundamentals(StockMetrics(dividend_yield_percentage=Decimal("0")))
    assert result.dividend is FundamentalCondition.NEUTRAL
