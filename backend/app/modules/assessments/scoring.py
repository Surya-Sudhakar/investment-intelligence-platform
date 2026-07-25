from datetime import UTC, datetime
from decimal import Decimal

from app.modules.assessments.config import TECHNICAL_V1, TechnicalV1Config
from app.modules.assessments.schemas import (
    AssessmentFactor,
    ComponentScore,
    DataQualityInformation,
    RiskAssessment,
    RiskComponent,
    RiskLevel,
    TechnicalAssessment,
    TechnicalAssessmentState,
    TimeHorizon,
)
from app.modules.intelligence.schemas import (
    FreshnessState,
    IntelligenceSnapshot,
    MarketState,
    MomentumState,
    TrendState,
)
from app.modules.market_data.schemas import Interval

HUNDRED = Decimal("100")


def _clamp(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return max(minimum, min(maximum, value))


def _component(
    name: str,
    weight: int,
    raw: str | float | None,
    signal: float | None,
    explanation: str,
) -> ComponentScore:
    return ComponentScore(
        name=name,
        weight=weight,
        available=signal is not None,
        raw_value=raw,
        signal=signal,
        weighted_contribution=round(weight * signal, 4) if signal is not None else None,
        explanation=explanation,
    )


def _trend(snapshot: IntelligenceSnapshot, config: TechnicalV1Config) -> ComponentScore:
    signals = {
        TrendState.STRONG_UPTREND: 1.0,
        TrendState.UPTREND: 0.6,
        TrendState.SIDEWAYS: 0.0,
        TrendState.DOWNTREND: -0.6,
        TrendState.STRONG_DOWNTREND: -1.0,
        TrendState.UNKNOWN: None,
    }
    signal = signals[snapshot.trend]
    return _component(
        "trend",
        config.trend_weight,
        snapshot.trend.value,
        signal,
        f"The Phase 3 trend classification is {snapshot.trend.value}.",
    )


def _momentum(snapshot: IntelligenceSnapshot, config: TechnicalV1Config) -> ComponentScore:
    signals = {
        MomentumState.STRONG_BULLISH: 1.0,
        MomentumState.BULLISH: 0.5,
        MomentumState.NEUTRAL: 0.0,
        MomentumState.BEARISH: -0.5,
        MomentumState.STRONG_BEARISH: -1.0,
        MomentumState.UNKNOWN: None,
    }
    signal = signals[snapshot.momentum]
    return _component(
        "momentum",
        config.momentum_weight,
        snapshot.momentum.value,
        signal,
        f"The Phase 3 momentum classification is {snapshot.momentum.value}.",
    )


def _price_ema(snapshot: IntelligenceSnapshot, config: TechnicalV1Config) -> ComponentScore:
    price = snapshot.quote.price
    ema20 = snapshot.indicators.ema20
    ema50 = snapshot.indicators.ema50
    if ema20 is None or ema50 is None:
        return _component(
            "price_vs_ema",
            config.price_ema_weight,
            None,
            None,
            "Price-to-EMA scoring requires EMA20 and EMA50.",
        )
    above = int(price > ema20) + int(price > ema50)
    below = int(price < ema20) + int(price < ema50)
    signal = 1.0 if above == 2 else 0.35 if above == 1 else -1.0 if below == 2 else -0.35
    return _component(
        "price_vs_ema",
        config.price_ema_weight,
        float(price),
        signal,
        "Price is compared independently with EMA20 and EMA50.",
    )


def _ema_alignment(snapshot: IntelligenceSnapshot, config: TechnicalV1Config) -> ComponentScore:
    ema20 = snapshot.indicators.ema20
    ema50 = snapshot.indicators.ema50
    if ema20 is None or ema50 is None or ema50 == 0:
        return _component(
            "ema_alignment",
            config.ema_alignment_weight,
            None,
            None,
            "EMA alignment requires non-zero EMA20 and EMA50.",
        )
    spread = float((ema20 - ema50) / ema50 * HUNDRED)
    if spread >= config.ema_strong_spread_pct:
        signal = 1.0
    elif spread >= config.ema_moderate_spread_pct:
        signal = 0.5
    elif spread <= -config.ema_strong_spread_pct:
        signal = -1.0
    elif spread <= -config.ema_moderate_spread_pct:
        signal = -0.5
    else:
        signal = 0.0
    return _component(
        "ema_alignment",
        config.ema_alignment_weight,
        spread,
        signal,
        "EMA20 is evaluated as a percentage above or below EMA50.",
    )


def _rsi(snapshot: IntelligenceSnapshot, config: TechnicalV1Config) -> ComponentScore:
    value = snapshot.indicators.rsi14
    if value is None:
        return _component("rsi14", config.rsi_weight, None, None, "RSI14 is unavailable.")
    raw = float(value)
    oversold, weak, neutral_low, neutral_high, strong, overbought = config.rsi_boundaries
    if raw >= overbought:
        signal = 0.4
    elif raw >= strong:
        signal = 1.0
    elif raw >= neutral_high:
        signal = 0.6
    elif raw >= neutral_low:
        signal = 0.0
    elif raw >= weak:
        signal = -0.6
    elif raw >= oversold:
        signal = -1.0
    else:
        signal = -0.4
    return _component(
        "rsi14",
        config.rsi_weight,
        raw,
        signal,
        "RSI measures directional momentum; extreme values also add extension risk.",
    )


def _levels(snapshot: IntelligenceSnapshot, config: TechnicalV1Config) -> ComponentScore:
    support = snapshot.support_resistance.distance_to_support_percentage
    resistance = snapshot.support_resistance.distance_to_resistance_percentage
    if support is not None and resistance is not None:
        denominator = support + resistance
        signal = float((resistance - support) / denominator) if denominator > 0 else 0.0
        raw = signal
    elif support is not None:
        signal = 0.25 if support <= Decimal(str(config.close_level_pct)) else 0.0
        raw = float(support)
    elif resistance is not None:
        signal = -0.25 if resistance <= Decimal(str(config.close_level_pct)) else 0.0
        raw = float(resistance)
    else:
        return _component(
            "support_resistance",
            config.levels_weight,
            None,
            None,
            "No calculated support or resistance distance is available.",
        )
    return _component(
        "support_resistance",
        config.levels_weight,
        raw,
        _clamp(signal, -1, 1),
        "Relative room to calculated support and resistance is compared.",
    )


def _range_position(snapshot: IntelligenceSnapshot, config: TechnicalV1Config) -> ComponentScore:
    high = snapshot.indicators.high_52_week
    low = snapshot.indicators.low_52_week
    price = snapshot.quote.price
    if high is None or low is None or high <= low:
        return _component(
            "range_position",
            config.range_position_weight,
            None,
            None,
            "A valid 52-week high and low are required.",
        )
    position = float((price - low) / (high - low))
    lower, lower_mid, upper_mid, upper = config.range_position_boundaries
    if position >= upper:
        signal = 0.75
    elif position >= upper_mid:
        signal = 0.4
    elif position >= lower_mid:
        signal = 0.0
    elif position >= lower:
        signal = -0.4
    else:
        signal = -0.75
    return _component(
        "range_position",
        config.range_position_weight,
        position,
        signal,
        "Price position is measured within the calculated 52-week range.",
    )


def _scaled_component(
    name: str,
    value: Decimal | None,
    scale: float,
    weight: int,
    explanation: str,
) -> ComponentScore:
    if value is None:
        return _component(name, weight, None, None, f"{name} is unavailable.")
    raw = float(value)
    return _component(name, weight, raw, _clamp(raw / scale, -1, 1), explanation)


def _volume(snapshot: IntelligenceSnapshot, config: TechnicalV1Config) -> ComponentScore:
    volume = snapshot.quote.volume
    average = snapshot.indicators.average_volume
    change = snapshot.indicators.daily_change_percentage
    if (
        volume is None
        or average is None
        or average <= 0
        or change is None
        or snapshot.market_status.state not in {MarketState.CLOSED, MarketState.HOLIDAY}
    ):
        return _component(
            "volume_confirmation",
            config.volume_confirmation_weight,
            None,
            None,
            "Completed-session quote volume and average volume are required.",
        )
    ratio = Decimal(volume) / average
    moderate, strong = config.volume_ratio_boundaries
    magnitude = (
        1.0 if ratio >= Decimal(str(strong)) else 0.5 if ratio >= Decimal(str(moderate)) else 0.0
    )
    signal = magnitude if change > 0 else -magnitude if change < 0 else 0.0
    return _component(
        "volume_confirmation",
        config.volume_confirmation_weight,
        float(ratio),
        signal,
        "Completed-session volume is compared with average volume.",
    )


def directional_components(
    snapshot: IntelligenceSnapshot, config: TechnicalV1Config = TECHNICAL_V1
) -> list[ComponentScore]:
    return [
        _trend(snapshot, config),
        _momentum(snapshot, config),
        _price_ema(snapshot, config),
        _ema_alignment(snapshot, config),
        _rsi(snapshot, config),
        _levels(snapshot, config),
        _range_position(snapshot, config),
        _scaled_component(
            "daily_change",
            snapshot.indicators.daily_change_percentage,
            config.daily_change_scale_pct,
            config.daily_change_weight,
            "Daily change is scaled and clamped at three percent.",
        ),
        _volume(snapshot, config),
        _scaled_component(
            "opening_gap",
            snapshot.indicators.gap_percentage,
            config.gap_scale_pct,
            config.opening_gap_weight,
            "The opening gap is scaled and clamped at two percent.",
        ),
    ]


def _assessment(score: int, config: TechnicalV1Config) -> TechnicalAssessmentState:
    if score >= config.strongly_bullish_min:
        return TechnicalAssessmentState.STRONGLY_BULLISH
    if score >= config.bullish_min:
        return TechnicalAssessmentState.BULLISH
    if score >= config.neutral_min:
        return TechnicalAssessmentState.NEUTRAL
    if score >= config.bearish_min:
        return TechnicalAssessmentState.BEARISH
    return TechnicalAssessmentState.STRONGLY_BEARISH


FRESHNESS_QUALITY = {
    FreshnessState.LIVE: 100,
    FreshnessState.MARKET_CLOSED: 95,
    FreshnessState.DELAYED: 70,
    FreshnessState.FALLBACK: 45,
    FreshnessState.STALE: 25,
    FreshnessState.UNKNOWN: 20,
    FreshnessState.DISCONNECTED: 0,
}

FRESHNESS_RISK = {
    FreshnessState.LIVE: 10,
    FreshnessState.MARKET_CLOSED: 15,
    FreshnessState.DELAYED: 35,
    FreshnessState.FALLBACK: 65,
    FreshnessState.STALE: 75,
    FreshnessState.UNKNOWN: 60,
    FreshnessState.DISCONNECTED: 100,
}


def confidence_score(
    snapshot: IntelligenceSnapshot,
    components: list[ComponentScore],
    config: TechnicalV1Config = TECHNICAL_V1,
) -> tuple[int, float, list[str]]:
    available = [component for component in components if component.signal is not None]
    available_weight = sum(component.weight for component in available)
    coverage = available_weight / config.directional_total_weight * 100
    directional_mass = sum(component.weight * abs(component.signal or 0) for component in available)
    net = abs(sum(component.weight * (component.signal or 0) for component in available))
    agreement = (
        100
        if directional_mass == 0 and available
        else (net / directional_mass * 100 if directional_mass else 0)
    )
    value = (
        config.confidence_coverage_weight * coverage
        + config.confidence_freshness_weight * FRESHNESS_QUALITY[snapshot.freshness.state]
        + config.confidence_agreement_weight * agreement
    )
    issues: list[str] = []
    if snapshot.market_status.state is MarketState.UNKNOWN:
        value -= config.unknown_market_confidence_penalty
        issues.append("Market status is unknown.")
    high = snapshot.indicators.high_52_week
    low = snapshot.indicators.low_52_week
    if high is not None and low is not None and high <= low:
        value -= config.invalid_relationship_confidence_penalty
        issues.append("The 52-week high/low relationship is invalid.")
    return round(_clamp(value)), round(coverage, 2), issues


def _risk_component(
    name: str,
    weight: int,
    raw: str | float | None,
    value: float | None,
    explanation: str,
) -> RiskComponent:
    return RiskComponent(
        name=name,
        weight=weight,
        available=value is not None,
        raw_value=raw,
        risk_value=value,
        weighted_contribution=round(weight * value, 4) if value is not None else None,
        explanation=explanation,
    )


def risk_components(
    snapshot: IntelligenceSnapshot, config: TechnicalV1Config = TECHNICAL_V1
) -> list[RiskComponent]:
    price = snapshot.quote.price
    atr = snapshot.indicators.atr14
    if atr is None or price <= 0:
        atr_component = _risk_component(
            "atr_volatility", config.risk_atr_weight, None, None, "ATR14 is unavailable."
        )
    else:
        atr_pct = float(atr / price * HUNDRED)
        atr_very_low, atr_low, atr_moderate, atr_high = config.atr_risk_boundaries_pct
        if atr_pct < atr_very_low:
            value = 10
        elif atr_pct < atr_low:
            value = 20
        elif atr_pct < atr_moderate:
            value = 40
        elif atr_pct < atr_high:
            value = 75
        else:
            value = 100
        atr_component = _risk_component(
            "atr_volatility",
            config.risk_atr_weight,
            atr_pct,
            value,
            "ATR14 is evaluated as a percentage of price.",
        )
    support = snapshot.support_resistance.distance_to_support_percentage
    if support is None:
        support_component = _risk_component(
            "support_distance", config.risk_support_weight, None, None, "Support is unavailable."
        )
    else:
        raw_support = float(support)
        close, moderate, distant = config.support_risk_boundaries_pct
        if raw_support <= close:
            value = 20
        elif raw_support <= moderate:
            value = 35
        elif raw_support <= distant:
            value = 60
        else:
            value = 80
        support_component = _risk_component(
            "support_distance",
            config.risk_support_weight,
            raw_support,
            value,
            "Greater downside distance to support increases structural risk.",
        )
    distances = [
        float(value)
        for value in (
            snapshot.support_resistance.distance_to_support_percentage,
            snapshot.support_resistance.distance_to_resistance_percentage,
        )
        if value is not None
    ]
    if not distances:
        proximity_component = _risk_component(
            "level_proximity",
            config.risk_level_proximity_weight,
            None,
            None,
            "No calculated level distance is available.",
        )
    else:
        nearest = min(distances)
        close, near, moderate = config.proximity_risk_boundaries_pct
        value = (
            80 if nearest <= close else 65 if nearest <= near else 45 if nearest <= moderate else 25
        )
        if snapshot.support_resistance.breakout_risk:
            value = max(value, config.breakout_risk_floor)
        proximity_component = _risk_component(
            "level_proximity",
            config.risk_level_proximity_weight,
            nearest,
            value,
            "Proximity to a calculated level increases breakout uncertainty.",
        )
    change = snapshot.indicators.daily_change_percentage
    move_component = _absolute_risk(
        "daily_move",
        change,
        config.risk_daily_move_weight,
        config.daily_move_risk_boundaries_pct,
    )
    gap_component = _absolute_risk(
        "opening_gap",
        snapshot.indicators.gap_percentage,
        config.risk_gap_weight,
        config.opening_gap_risk_boundaries_pct,
    )
    high = snapshot.indicators.high_52_week
    low = snapshot.indicators.low_52_week
    if high is None or low is None or high <= low:
        range_component = _risk_component(
            "range_extreme",
            config.risk_range_extreme_weight,
            None,
            None,
            "A valid 52-week range is unavailable.",
        )
    else:
        distance = min(
            abs(float((price - high) / high * HUNDRED)),
            abs(float((price - low) / low * HUNDRED)),
        )
        close, near = config.range_extreme_risk_boundaries_pct
        value = 70 if distance <= close else 45 if distance <= near else 20
        range_component = _risk_component(
            "range_extreme",
            config.risk_range_extreme_weight,
            distance,
            value,
            "Proximity to either 52-week extreme is measured.",
        )
    if snapshot.market_status.state in {
        MarketState.OPEN,
        MarketState.CLOSED,
        MarketState.HOLIDAY,
    }:
        market_risk = 10
    elif snapshot.market_status.state in {
        MarketState.PRE_MARKET,
        MarketState.AFTER_HOURS,
    }:
        market_risk = 40
    else:
        market_risk = 70
    return [
        atr_component,
        _risk_component(
            "freshness",
            config.risk_freshness_weight,
            snapshot.freshness.state.value,
            FRESHNESS_RISK[snapshot.freshness.state],
            "Data-delivery quality contributes independently to risk.",
        ),
        support_component,
        proximity_component,
        move_component,
        gap_component,
        range_component,
        _risk_component(
            "market_status",
            config.risk_market_status_weight,
            snapshot.market_status.state.value,
            market_risk,
            "Uncertain or extended sessions increase assessment risk.",
        ),
    ]


def _absolute_risk(
    name: str, value: Decimal | None, weight: int, bands: tuple[int, int, int]
) -> RiskComponent:
    if value is None:
        return _risk_component(name, weight, None, None, f"{name} is unavailable.")
    raw = abs(float(value))
    risk = 20 if raw < bands[0] else 40 if raw < bands[1] else 70 if raw < bands[2] else 100
    return _risk_component(name, weight, raw, risk, f"Absolute {name} magnitude is evaluated.")


def _risk_level(score: int, config: TechnicalV1Config) -> RiskLevel:
    if score >= config.risk_extreme_min:
        return RiskLevel.EXTREME
    if score >= config.risk_high_min:
        return RiskLevel.HIGH
    if score >= config.risk_elevated_min:
        return RiskLevel.ELEVATED
    if score >= config.risk_moderate_min:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def build_assessment(
    snapshot: IntelligenceSnapshot,
    generated_at: datetime | None = None,
    config: TechnicalV1Config = TECHNICAL_V1,
) -> TechnicalAssessment:
    components = directional_components(snapshot, config)
    available = [component for component in components if component.signal is not None]
    available_weight = sum(component.weight for component in available)
    net = sum(component.weight * (component.signal or 0) for component in available)
    score = round(_clamp(50 + 50 * net / available_weight)) if available_weight else 50
    assessment = _assessment(score, config)
    confidence, coverage, issues = confidence_score(snapshot, components, config)
    risk_items = risk_components(snapshot, config)
    available_risk = [component for component in risk_items if component.risk_value is not None]
    risk_weight = sum(component.weight for component in available_risk)
    risk_score = (
        round(
            sum(component.weight * (component.risk_value or 0) for component in available_risk)
            / risk_weight
        )
        if risk_weight
        else 0
    )
    risk_coverage = risk_weight / config.risk_total_weight * 100
    direction = 1 if score >= config.bullish_min else -1 if score < config.neutral_min else 0
    supporting: list[AssessmentFactor] = []
    conflicting: list[AssessmentFactor] = []
    missing: list[AssessmentFactor] = []
    for component in components:
        if component.signal is None:
            missing.append(
                AssessmentFactor(
                    code=f"MISSING_{component.name.upper()}",
                    message=component.explanation,
                )
            )
        elif abs(component.signal) >= 0.25:
            factor = AssessmentFactor(
                code=component.name.upper(),
                message=component.explanation,
            )
            if direction == 0 or component.signal * direction > 0:
                supporting.append(factor)
            else:
                conflicting.append(factor)
    risk_factors = [
        AssessmentFactor(code=item.name.upper(), message=item.explanation)
        for item in available_risk
        if (item.risk_value or 0) >= 60
    ]
    return TechnicalAssessment(
        symbol=snapshot.symbol,
        interval=Interval.ONE_DAY,
        time_horizon=TimeHorizon.SWING_POSITION,
        assessment=assessment,
        technical_score=score,
        confidence_score=confidence,
        risk=RiskAssessment(
            score=risk_score,
            level=_risk_level(risk_score, config),
            data_coverage_percentage=round(risk_coverage, 2),
            components=risk_items,
        ),
        components=components,
        supporting_factors=supporting,
        conflicting_factors=conflicting,
        risk_factors=risk_factors,
        missing_data_factors=missing,
        data_quality=DataQualityInformation(
            freshness_state=snapshot.freshness.state,
            source_age_seconds=snapshot.freshness.age_seconds,
            quote_data_status=snapshot.quote.data_status,
            quote_cached=snapshot.quote.cached,
            market_status=snapshot.market_status.state,
            available_directional_weight=available_weight,
            eligible_directional_weight=config.directional_total_weight,
            input_coverage_percentage=coverage,
            issues=issues,
        ),
        scoring_version=config.version,
        snapshot_timestamp=snapshot.timestamp,
        generated_at=generated_at or datetime.now(UTC),
    )
