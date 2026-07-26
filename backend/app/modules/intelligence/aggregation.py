from datetime import UTC, datetime

from app.modules.market_data.schemas import Candle, Interval, Quote

INTERVAL_SECONDS = {
    Interval.FIVE_MINUTES: 300,
    Interval.FIFTEEN_MINUTES: 900,
    Interval.ONE_HOUR: 3600,
    Interval.ONE_DAY: 86400,
}


def bucket_start(timestamp: datetime, interval: Interval) -> datetime:
    utc = timestamp.astimezone(UTC)
    seconds = int(utc.timestamp())
    return datetime.fromtimestamp(seconds - seconds % INTERVAL_SECONDS[interval], UTC)


class CandleAggregator:
    def __init__(self) -> None:
        self._candles: dict[tuple[str, Interval, datetime], Candle] = {}
        self._quotes: set[tuple[str, datetime]] = set()

    def add(self, quote: Quote, interval: Interval) -> Candle:
        quote_key = (quote.symbol, quote.timestamp)
        start = bucket_start(quote.timestamp, interval)
        key = (quote.symbol, interval, start)
        if quote_key in self._quotes and key in self._candles:
            return self._candles[key]
        self._quotes.add(quote_key)
        existing = self._candles.get(key)
        volume = quote.volume
        if existing:
            candle = existing.model_copy(
                update={
                    "high": max(existing.high, quote.price),
                    "low": min(existing.low, quote.price),
                    "close": quote.price
                    if quote.timestamp >= existing.source_timestamp
                    else existing.close,
                    "volume": max(existing.volume or 0, volume or 0) or None,
                    "source_timestamp": max(existing.source_timestamp, quote.timestamp),
                    "received_at": max(existing.received_at, quote.received_at),
                }
            )
        else:
            candle = Candle(
                symbol=quote.symbol,
                interval=interval,
                time=start,
                open=quote.price,
                high=quote.price,
                low=quote.price,
                close=quote.price,
                volume=volume,
                is_complete=False,
                provider=quote.provider,
                source_timestamp=quote.timestamp,
                received_at=quote.received_at,
                data_status=quote.data_status,
            )
        self._candles[key] = candle
        return candle

    def candles(self, symbol: str, interval: Interval) -> list[Candle]:
        return sorted(
            [
                candle
                for (item_symbol, item_interval, _), candle in self._candles.items()
                if item_symbol == symbol and item_interval == interval
            ],
            key=lambda candle: candle.time,
        )

    def finalize_before(self, moment: datetime) -> None:
        for key, candle in self._candles.items():
            end = candle.time.timestamp() + INTERVAL_SECONDS[candle.interval]
            if end <= moment.astimezone(UTC).timestamp():
                self._candles[key] = candle.model_copy(update={"is_complete": True})

    def close_market(self, symbol: str) -> None:
        for key, candle in self._candles.items():
            if candle.symbol == symbol:
                self._candles[key] = candle.model_copy(update={"is_complete": True})
