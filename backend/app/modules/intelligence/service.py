import logging
from datetime import UTC, datetime, time

from app.core.config import Settings
from app.core.exceptions import MarketDataError
from app.modules.intelligence.freshness import classify_freshness
from app.modules.intelligence.indicators import calculate_indicators
from app.modules.intelligence.market_status import ExchangeSchedule, determine_market_status
from app.modules.intelligence.polling import QuotePollingEngine
from app.modules.intelligence.schemas import (
    IntelligenceHealth,
    IntelligenceSnapshot,
    MarketState,
    MarketStatusResult,
)
from app.modules.intelligence.signals import (
    detect_momentum,
    detect_support_resistance,
    detect_trend,
    detect_volatility,
)
from app.modules.market_data.schemas import Interval, ProviderHealth, SymbolDetails
from app.modules.market_data.service import MarketDataService

logger = logging.getLogger(__name__)


def _schedule(details: SymbolDetails) -> ExchangeSchedule | None:
    if not details.timezone or not details.market_open_time or not details.market_close_time:
        return None
    try:
        return ExchangeSchedule(
            timezone=details.timezone,
            open_time=time.fromisoformat(details.market_open_time),
            close_time=time.fromisoformat(details.market_close_time),
        )
    except ValueError:
        return None


class IntelligenceService:
    def __init__(
        self,
        market_data: MarketDataService,
        polling: QuotePollingEngine,
        settings: Settings,
    ) -> None:
        self.market_data = market_data
        self.polling = polling
        self.settings = settings

    async def snapshot(self, symbol: str) -> IntelligenceSnapshot:
        now = datetime.now(UTC)
        quote = await self.market_data.quote(symbol)
        try:
            details = await self.market_data.symbol_details(symbol)
            schedule = _schedule(details)
        except MarketDataError as exc:
            logger.warning(
                "Symbol schedule unavailable for intelligence snapshot",
                extra={"symbol": quote.symbol, "error_code": exc.code},
            )
            schedule = None
        market_status = determine_market_status(schedule, now)
        if market_status.state is MarketState.UNKNOWN and quote.market_open is not None:
            state = MarketState.OPEN if quote.market_open else MarketState.CLOSED
            market_status = MarketStatusResult(
                state=state,
                exchange_timezone=None,
                evaluated_at=now,
                reason="Market status was supplied by the market-data provider.",
            )
        try:
            response = await self.market_data.candles(
                symbol,
                Interval.ONE_DAY,
                None,
                None,
                self.settings.intelligence_candle_lookback,
            )
            candles = response.data.candles
        except MarketDataError as exc:
            logger.warning(
                "Historical candles unavailable for intelligence snapshot",
                extra={"symbol": quote.symbol, "error_code": exc.code},
            )
            candles = []
        indicators = calculate_indicators(candles)
        freshness = classify_freshness(
            source_timestamp=quote.timestamp,
            received_at=quote.received_at,
            provider_delayed=quote.delayed,
            market_status=market_status.state,
            provider_reachable=True,
            live_threshold_seconds=self.settings.intelligence_live_threshold_seconds,
            stale_threshold_seconds=self.settings.intelligence_stale_threshold_seconds,
            evaluated_at=now,
        )
        return IntelligenceSnapshot(
            symbol=quote.symbol,
            quote=quote,
            freshness=freshness,
            market_status=market_status,
            trend=detect_trend(quote.price, indicators),
            momentum=detect_momentum(indicators),
            volatility=detect_volatility(quote.price, indicators),
            indicators=indicators,
            support_resistance=detect_support_resistance(candles, quote.price),
            provider=quote.provider,
            timestamp=now,
        )

    async def health(self) -> IntelligenceHealth:
        checked_at = datetime.now(UTC)
        provider: ProviderHealth = await self.market_data.health()
        healthy = provider.configured and provider.reachable
        return IntelligenceHealth(
            status="healthy" if healthy else "unavailable",
            market_data_configured=provider.configured,
            provider_reachable=provider.reachable,
            polling_jobs=self.polling.active_count,
            checked_at=checked_at,
            message="Intelligence service is ready." if healthy else provider.message,
        )
