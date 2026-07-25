# Phase 3 market intelligence

Phase 3 converts provider quotes and daily candles into a deterministic, normalized snapshot. It does not predict prices or produce trading recommendations.

## API

- `GET /api/v1/intelligence/{symbol}` returns the quote, freshness, exchange status, indicators, trend, momentum, volatility, support/resistance, provider, and calculation timestamp.
- `GET /api/v1/intelligence/health` reports provider readiness and active polling jobs.

The service uses `SymbolDetails` exchange timezone and session times when the provider supplies them. Otherwise market status is deliberately `UNKNOWN`; it never assumes US hours.

## Configuration

- `INTELLIGENCE_POLL_INTERVAL_SECONDS` (default `30`)
- `INTELLIGENCE_LIVE_THRESHOLD_SECONDS` (default `60`)
- `INTELLIGENCE_STALE_THRESHOLD_SECONDS` (default `900`)
- `INTELLIGENCE_CANDLE_LOOKBACK` (default `260`)

Polling is an in-process async facility with per-symbol task de-duplication and graceful shutdown. No polling jobs start merely by requesting a snapshot.

The reusable candle aggregator aligns buckets in UTC for 5-minute, 15-minute, hourly, and daily intervals. It keeps incomplete candles, ignores duplicate symbol/timestamp quotes, accepts out-of-order quotes without changing the latest close, and finalizes elapsed or market-closed buckets. Gaps remain gaps rather than fabricated candles.

Indicators are calculated with `Decimal` arithmetic: EMA20, EMA50, Wilder RSI14, Wilder ATR14, 20-session average volume, 52-week high/low (up to 252 sessions), daily change, previous close, and opening gap.

## Run

```powershell
docker compose up --build -d
docker compose run --rm backend alembic upgrade head
```

Open `http://localhost:3000`, then use the Market Intelligence section. A configured market-data API key is required for provider-backed snapshots.

## Test

```powershell
docker compose run --rm backend pytest
docker compose run --rm frontend npm test
docker compose run --rm frontend npm run lint
docker compose run --rm frontend npm run type-check
```
