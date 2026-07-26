from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class FundamentalThresholds:
    methodology_version: str = "fundamentals-v1"
    strong_profit_margin: Decimal = Decimal("20")
    strong_operating_margin: Decimal = Decimal("15")
    strong_growth: Decimal = Decimal("15")
    positive_growth: Decimal = Decimal("5")
    weak_growth: Decimal = Decimal("-5")
    strong_debt_to_equity: Decimal = Decimal("50")
    positive_debt_to_equity: Decimal = Decimal("100")
    neutral_debt_to_equity: Decimal = Decimal("200")
    strong_pe: Decimal = Decimal("15")
    positive_pe: Decimal = Decimal("25")
    neutral_pe: Decimal = Decimal("40")
    strong_dividend_yield: Decimal = Decimal("4")
    positive_dividend_yield: Decimal = Decimal("2")
    minimum_overall_components: int = 3
    strong_overall: Decimal = Decimal("2.5")
    positive_overall: Decimal = Decimal("1.75")
    neutral_overall: Decimal = Decimal("0.75")


FUNDAMENTALS_V1 = FundamentalThresholds()
