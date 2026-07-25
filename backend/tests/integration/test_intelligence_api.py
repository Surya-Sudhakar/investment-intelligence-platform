from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app
from app.modules.intelligence.dependencies import get_intelligence_service
from app.modules.intelligence.schemas import (
    FreshnessMetadata,
    FreshnessState,
    IndicatorSet,
    IntelligenceHealth,
    IntelligenceSnapshot,
    MarketState,
    MarketStatusResult,
    MomentumState,
    SupportResistance,
    TrendState,
    VolatilityState,
)
from app.modules.market_data.schemas import DataStatus, Quote

NOW = datetime(2026, 7, 24, 12, tzinfo=UTC)


class FakeIntelligenceService:
    async def health(self) -> IntelligenceHealth:
        return IntelligenceHealth(
            status="healthy",
            market_data_configured=True,
            provider_reachable=True,
            polling_jobs=0,
            checked_at=NOW,
            message="ready",
        )

    async def snapshot(self, symbol: str) -> IntelligenceSnapshot:
        quote = Quote(
            symbol=symbol.upper(),
            price=Decimal("100"),
            timestamp=NOW,
            received_at=NOW,
            provider="test",
            delayed=False,
            data_status=DataStatus.UNKNOWN,
            age_seconds=0,
        )
        return IntelligenceSnapshot(
            symbol=symbol.upper(),
            quote=quote,
            freshness=FreshnessMetadata(
                state=FreshnessState.LIVE,
                age_seconds=0,
                threshold_seconds=900,
                source_timestamp=NOW,
                evaluated_at=NOW,
                reason="fresh",
            ),
            market_status=MarketStatusResult(
                state=MarketState.OPEN,
                exchange_timezone="UTC",
                evaluated_at=NOW,
                reason="open",
            ),
            trend=TrendState.UPTREND,
            momentum=MomentumState.BULLISH,
            volatility=VolatilityState.NORMAL,
            indicators=IndicatorSet(
                ema20=Decimal("99"),
                ema50=Decimal("98"),
                rsi14=Decimal("60"),
                atr14=Decimal("2"),
                average_volume=Decimal("1000"),
                high_52_week=Decimal("110"),
                low_52_week=Decimal("80"),
                daily_change_percentage=Decimal("1"),
                previous_close=Decimal("99"),
                gap_percentage=Decimal("0"),
            ),
            support_resistance=SupportResistance(
                nearest_support=Decimal("95"),
                nearest_resistance=Decimal("105"),
                distance_to_support_percentage=Decimal("5"),
                distance_to_resistance_percentage=Decimal("5"),
                breakout_risk=False,
            ),
            provider="test",
            timestamp=NOW,
        )


def test_intelligence_endpoints(client: TestClient) -> None:
    app.dependency_overrides[get_intelligence_service] = lambda: FakeIntelligenceService()
    snapshot = client.get("/api/v1/intelligence/aapl")
    health = client.get("/api/v1/intelligence/health")
    assert snapshot.status_code == 200
    assert snapshot.json()["symbol"] == "AAPL"
    assert snapshot.json()["trend"] == "UPTREND"
    assert health.status_code == 200
    assert health.json()["polling_jobs"] == 0
