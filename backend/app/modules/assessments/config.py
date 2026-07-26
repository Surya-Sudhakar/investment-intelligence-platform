from dataclasses import dataclass


@dataclass(frozen=True)
class TechnicalV1Config:
    version: str = "technical-v1"
    trend_weight: int = 20
    momentum_weight: int = 15
    price_ema_weight: int = 15
    ema_alignment_weight: int = 10
    rsi_weight: int = 10
    levels_weight: int = 10
    range_position_weight: int = 8
    daily_change_weight: int = 5
    volume_confirmation_weight: int = 4
    opening_gap_weight: int = 3
    strongly_bullish_min: int = 80
    bullish_min: int = 60
    neutral_min: int = 40
    bearish_min: int = 20
    ema_strong_spread_pct: float = 2.0
    ema_moderate_spread_pct: float = 0.5
    rsi_boundaries: tuple[int, ...] = (30, 40, 45, 55, 60, 70)
    range_position_boundaries: tuple[float, ...] = (0.2, 0.4, 0.6, 0.8)
    volume_ratio_boundaries: tuple[float, ...] = (0.75, 1.0)
    daily_change_scale_pct: float = 3.0
    gap_scale_pct: float = 2.0
    close_level_pct: float = 2.0
    confidence_coverage_weight: float = 0.60
    confidence_freshness_weight: float = 0.25
    confidence_agreement_weight: float = 0.15
    unknown_market_confidence_penalty: float = 5.0
    invalid_relationship_confidence_penalty: float = 10.0
    risk_atr_weight: int = 30
    risk_freshness_weight: int = 20
    risk_support_weight: int = 15
    risk_level_proximity_weight: int = 10
    risk_daily_move_weight: int = 10
    risk_gap_weight: int = 5
    risk_range_extreme_weight: int = 5
    risk_market_status_weight: int = 5
    atr_risk_boundaries_pct: tuple[float, ...] = (0.5, 1.0, 2.5, 5.0)
    support_risk_boundaries_pct: tuple[float, ...] = (2.0, 5.0, 10.0)
    proximity_risk_boundaries_pct: tuple[float, ...] = (0.5, 1.0, 2.0)
    daily_move_risk_boundaries_pct: tuple[int, int, int] = (1, 3, 5)
    opening_gap_risk_boundaries_pct: tuple[int, int, int] = (1, 2, 5)
    range_extreme_risk_boundaries_pct: tuple[float, float] = (2.0, 5.0)
    breakout_risk_floor: int = 70
    risk_moderate_min: int = 20
    risk_elevated_min: int = 40
    risk_high_min: int = 60
    risk_extreme_min: int = 80

    @property
    def directional_total_weight(self) -> int:
        return (
            self.trend_weight
            + self.momentum_weight
            + self.price_ema_weight
            + self.ema_alignment_weight
            + self.rsi_weight
            + self.levels_weight
            + self.range_position_weight
            + self.daily_change_weight
            + self.volume_confirmation_weight
            + self.opening_gap_weight
        )

    @property
    def risk_total_weight(self) -> int:
        return (
            self.risk_atr_weight
            + self.risk_freshness_weight
            + self.risk_support_weight
            + self.risk_level_proximity_weight
            + self.risk_daily_move_weight
            + self.risk_gap_weight
            + self.risk_range_extreme_weight
            + self.risk_market_status_weight
        )


TECHNICAL_V1 = TechnicalV1Config()
