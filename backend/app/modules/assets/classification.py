from decimal import Decimal

from app.modules.assets.config import FUNDAMENTALS_V1, FundamentalThresholds
from app.modules.assets.schemas import (
    FundamentalCondition,
    StockFundamentalClassification,
    StockMetrics,
)


def _profitability(metrics: StockMetrics, cfg: FundamentalThresholds) -> FundamentalCondition:
    profit, operating = metrics.profit_margin_percentage, metrics.operating_margin_percentage
    if profit is None and operating is None:
        return FundamentalCondition.UNAVAILABLE
    if profit is not None and operating is not None:
        if profit >= cfg.strong_profit_margin and operating >= cfg.strong_operating_margin:
            return FundamentalCondition.STRONG
        if profit > 0 and operating > 0:
            return FundamentalCondition.POSITIVE
    if (profit is not None and profit < 0) or (operating is not None and operating < 0):
        return FundamentalCondition.WEAK
    return FundamentalCondition.NEUTRAL


def _growth(value: Decimal | None, cfg: FundamentalThresholds) -> FundamentalCondition:
    if value is None:
        return FundamentalCondition.UNAVAILABLE
    if value >= cfg.strong_growth:
        return FundamentalCondition.STRONG
    if value >= cfg.positive_growth:
        return FundamentalCondition.POSITIVE
    if value <= cfg.weak_growth:
        return FundamentalCondition.WEAK
    return FundamentalCondition.NEUTRAL


def _debt(value: Decimal | None, cfg: FundamentalThresholds) -> FundamentalCondition:
    if value is None or value < 0:
        return FundamentalCondition.UNAVAILABLE
    if value <= cfg.strong_debt_to_equity:
        return FundamentalCondition.STRONG
    if value <= cfg.positive_debt_to_equity:
        return FundamentalCondition.POSITIVE
    if value <= cfg.neutral_debt_to_equity:
        return FundamentalCondition.NEUTRAL
    return FundamentalCondition.WEAK


def _valuation(value: Decimal | None, cfg: FundamentalThresholds) -> FundamentalCondition:
    if value is None:
        return FundamentalCondition.UNAVAILABLE
    if value <= 0 or value > cfg.neutral_pe:
        return FundamentalCondition.WEAK
    if value <= cfg.strong_pe:
        return FundamentalCondition.STRONG
    if value <= cfg.positive_pe:
        return FundamentalCondition.POSITIVE
    return FundamentalCondition.NEUTRAL


def _dividend(value: Decimal | None, cfg: FundamentalThresholds) -> FundamentalCondition:
    if value is None or value < 0:
        return FundamentalCondition.UNAVAILABLE
    if value >= cfg.strong_dividend_yield:
        return FundamentalCondition.STRONG
    if value >= cfg.positive_dividend_yield:
        return FundamentalCondition.POSITIVE
    return FundamentalCondition.NEUTRAL


def classify_fundamentals(
    metrics: StockMetrics, cfg: FundamentalThresholds = FUNDAMENTALS_V1
) -> StockFundamentalClassification:
    labels = [
        _profitability(metrics, cfg),
        _growth(metrics.revenue_growth_percentage, cfg),
        _debt(metrics.debt_to_equity, cfg),
        _valuation(metrics.pe_ratio, cfg),
        _dividend(metrics.dividend_yield_percentage, cfg),
    ]
    values = {
        FundamentalCondition.STRONG: Decimal(3),
        FundamentalCondition.POSITIVE: Decimal(2),
        FundamentalCondition.NEUTRAL: Decimal(1),
        FundamentalCondition.WEAK: Decimal(0),
    }
    available = [values[label] for label in labels if label in values]
    if len(available) < cfg.minimum_overall_components:
        overall = FundamentalCondition.UNAVAILABLE
    else:
        average = sum(available, Decimal(0)) / len(available)
        if average >= cfg.strong_overall:
            overall = FundamentalCondition.STRONG
        elif average >= cfg.positive_overall:
            overall = FundamentalCondition.POSITIVE
        elif average >= cfg.neutral_overall:
            overall = FundamentalCondition.NEUTRAL
        else:
            overall = FundamentalCondition.WEAK
    return StockFundamentalClassification(
        methodology_version=cfg.methodology_version,
        profitability=labels[0],
        growth=labels[1],
        debt=labels[2],
        valuation=labels[3],
        dividend=labels[4],
        overall=overall,
    )
