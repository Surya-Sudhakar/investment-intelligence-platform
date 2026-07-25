import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from app.modules.assessments.schemas import RiskLevel, TechnicalAssessmentState
from app.modules.assessments.scoring import build_assessment
from app.modules.assessments.service import AssessmentService
from app.modules.intelligence.schemas import (
    FreshnessMetadata,
    FreshnessState,
    IndicatorSet,
    IntelligenceSnapshot,
    MarketState,
    MarketStatusResult,
    MomentumState,
    SupportResistance,
    TrendState,
    VolatilityState,
)
from app.modules.market_data.schemas import DataStatus, Quote

NOW = datetime(2026, 7, 25, 12, tzinfo=UTC)


def snapshot(
    *,
    freshness: FreshnessState = FreshnessState.LIVE,
    trend: TrendState = TrendState.STRONG_UPTREND,
    momentum: MomentumState = MomentumState.STRONG_BULLISH,
    atr14: Decimal | None = Decimal("2"),
) -> IntelligenceSnapshot:
    return IntelligenceSnapshot(
        symbol="AAPL",
        quote=Quote(
            symbol="AAPL",
            price=Decimal("120"),
            volume=1_500,
            timestamp=NOW,
            received_at=NOW,
            provider="test",
            delayed=False,
            data_status=DataStatus.UNKNOWN,
            age_seconds=0,
        ),
        freshness=FreshnessMetadata(
            state=freshness,
            age_seconds=0,
            threshold_seconds=900,
            source_timestamp=NOW,
            evaluated_at=NOW,
            reason="test",
        ),
        market_status=MarketStatusResult(
            state=MarketState.OPEN,
            exchange_timezone="UTC",
            evaluated_at=NOW,
            reason="test",
        ),
        trend=trend,
        momentum=momentum,
        volatility=VolatilityState.NORMAL,
        indicators=IndicatorSet(
            ema20=Decimal("110"),
            ema50=Decimal("100"),
            rsi14=Decimal("65"),
            atr14=atr14,
            average_volume=Decimal("1000"),
            high_52_week=Decimal("125"),
            low_52_week=Decimal("70"),
            daily_change_percentage=Decimal("2"),
            previous_close=Decimal("117.65"),
            gap_percentage=Decimal("0.5"),
        ),
        support_resistance=SupportResistance(
            nearest_support=Decimal("110"),
            nearest_resistance=Decimal("125"),
            distance_to_support_percentage=Decimal("8.33"),
            distance_to_resistance_percentage=Decimal("4.17"),
            breakout_risk=False,
        ),
        provider="test",
        timestamp=NOW,
    )


def test_bullish_inputs_produce_strong_bullish_assessment() -> None:
    result = build_assessment(snapshot(), generated_at=NOW)
    assert result.assessment is TechnicalAssessmentState.STRONGLY_BULLISH
    assert 80 <= result.technical_score <= 100
    assert result.confidence_score >= 90
    assert result.scoring_version == "technical-v1"
    assert result.interval.value == "1day"
    assert result.supporting_factors


def test_missing_inputs_reduce_confidence_without_inventing_values() -> None:
    incomplete = snapshot().model_copy(
        update={
            "indicators": IndicatorSet(
                ema20=None,
                ema50=None,
                rsi14=None,
                atr14=None,
                average_volume=None,
                high_52_week=None,
                low_52_week=None,
                daily_change_percentage=None,
                previous_close=None,
                gap_percentage=None,
            )
        }
    )
    complete = build_assessment(snapshot(), generated_at=NOW)
    result = build_assessment(incomplete, generated_at=NOW)
    assert result.confidence_score < complete.confidence_score
    assert result.missing_data_factors
    assert any(component.raw_value is None for component in result.components)


def test_risk_is_independent_of_direction() -> None:
    bullish = build_assessment(snapshot(atr14=Decimal("12")), generated_at=NOW)
    bearish = build_assessment(
        snapshot(
            trend=TrendState.STRONG_DOWNTREND,
            momentum=MomentumState.STRONG_BEARISH,
            atr14=Decimal("12"),
        ),
        generated_at=NOW,
    )
    assert bullish.risk.score == bearish.risk.score
    assert bullish.risk.level in {RiskLevel.ELEVATED, RiskLevel.HIGH, RiskLevel.EXTREME}
    assert bullish.technical_score != bearish.technical_score


def test_service_requests_one_snapshot() -> None:
    class FakeIntelligence:
        def __init__(self) -> None:
            self.calls = 0

        async def snapshot(self, symbol: str) -> IntelligenceSnapshot:
            self.calls += 1
            assert symbol == "AAPL"
            return snapshot()

    intelligence = FakeIntelligence()
    service = AssessmentService(intelligence)  # type: ignore[arg-type]
    result = asyncio.run(service.assess("AAPL"))
    assert result.symbol == "AAPL"
    assert intelligence.calls == 1
