# Technical assessments

Phase 4A converts one normalized Phase 3 intelligence snapshot into a deterministic
technical outlook. It does not persist assessments and does not call a market-data provider
directly.

## API

`GET /api/v1/assessments/{symbol}?interval=1day` returns the assessment. The query parameter
defaults to `1day`; every other interval returns the standard `UNSUPPORTED_INTERVAL` error.
`GET /api/v1/assessments/health` reports whether its Phase 3 input service is ready.

Each request calls `IntelligenceService.snapshot()` once. That service continues to obtain
quotes, symbol details, and daily candles through `MarketDataService`, including its existing
in-process cache.

## Method

The immutable `technical-v1` configuration centralizes all weights and thresholds. Directional
components are trend, momentum, price versus EMA20/EMA50, EMA alignment, RSI14, calculated
levels, 52-week range position, daily change, volume confirmation, and opening gap. Missing
components are excluded from score normalization rather than filled with invented values.

The technical score is centered at 50 and normalized over available directional weight.
Confidence is a separate weighted combination of input coverage, freshness, and agreement,
with explicit penalties for uncertain market status or invalid relationships. Risk is calculated
independently from ATR as a percentage of price, freshness, downside distance to support,
level proximity, absolute daily move, absolute opening gap, 52-week extremes, and market status.

RSI overbought and oversold values represent directional momentum together with extension risk.
They are not treated as automatic reversal conditions.

## Output

The response contains:

- `assessment`, `technical_score`, `confidence_score`, and independent `risk`
- the daily interval and `SWING_POSITION` time horizon
- component-level inputs, weights, signals, contributions, and explanations
- supporting, conflicting, risk, and missing-data factors
- input coverage, freshness, quote status, cache flag, market status, and quality issues
- `technical-v1`, snapshot timestamp, and generation timestamp

The implementation is provider-neutral because it consumes only `IntelligenceSnapshot`.

## Technical outlook thresholds

- `STRONGLY_BULLISH`: technical score 80–100
- `BULLISH`: technical score 60–79
- `NEUTRAL`: technical score 40–59
- `BEARISH`: technical score 20–39
- `STRONGLY_BEARISH`: technical score 0–19

The technical score describes directional evidence. Confidence describes coverage, freshness,
and component agreement. Risk describes uncertainty and adverse-movement exposure independently
of direction. A high technical score therefore does not imply low risk.

## Data and security properties

- Only `interval=1day` is accepted by the public assessment endpoint.
- One assessment request produces one `IntelligenceService.snapshot()` call.
- Existing quote and candle cache behavior remains owned by `MarketDataService`.
- No API key is accepted from or returned to the frontend.
- No assessment data is written to PostgreSQL.
- No provider quota is consumed directly by the assessment module.
