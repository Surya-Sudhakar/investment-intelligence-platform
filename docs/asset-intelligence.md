# Phase 5 Asset Intelligence

Phase 5 identifies an instrument as `STOCK`, `GOLD`, `ETF`, or `UNKNOWN` and returns a
provider-neutral, asset-specific response. It does not alter the Phase 4A technical score and
does not produce BUY, SELL, or HOLD output.

## Architecture

```text
GET /api/v1/assets/{symbol}/intelligence
  -> AssetIntelligenceService
  -> AssetDataProvider (implemented by the configured market-data adapter)
  -> component TTL cache
  -> MarketDataService / IntelligenceService for current observations
```

`AssetDataProvider` is separate from `MarketDataProvider`, preserving the Phase 2 API contract.
Both protocols are implemented by the configured adapter and share the existing HTTP client,
timeout, retry, safe-error, and cache infrastructure.

## Classification rules

1. `XAUUSD`, `XAU/USD`, and `XAU-USD` normalize to the unambiguous `GOLD` instrument.
2. Other instruments use provider metadata such as `Common Stock` or `ETF`.
3. A gold-backed exchange-traded fund such as `GLD` remains an `ETF`.
4. Unsupported provider instrument types return `UNSUPPORTED_ASSET`; they are not guessed.

The public gold URL uses `XAUUSD` because slashes in path segments are not consistently
preserved by HTTP routers and proxies.

## Stock fundamental methodology

The immutable initial methodology is `fundamentals-v1`. Inputs use percentage points.

| Component | STRONG | POSITIVE | NEUTRAL | WEAK |
|---|---|---|---|---|
| Profitability | Profit margin >=20% and operating margin >=15% | Both positive | Remaining non-negative/mixed case | Either negative |
| Growth | Revenue growth >=15% | >=5% | Between -5% and 5% | <=-5% |
| Debt | Debt/equity <=50 | <=100 | <=200 | >200 |
| Valuation | Positive P/E <=15 | <=25 | <=40 | Non-positive or >40 |
| Dividend | Yield >=4% | >=2% | Valid yield below 2%, including zero | Invalid/negative is unavailable |

Missing inputs produce `UNAVAILABLE`, never zero. Overall condition requires at least three
available components and averages `STRONG=3`, `POSITIVE=2`, `NEUTRAL=1`, and `WEAK=0`:

- at least 2.5: `STRONG`
- at least 1.75: `POSITIVE`
- at least 0.75: `NEUTRAL`
- below 0.75: `WEAK`

These are simple cross-sector descriptive rules, not investment recommendations.

## Cache strategy

| Component | Default TTL |
|---|---:|
| Asset classification | 24 hours |
| Company and ETF profiles | 24 hours |
| Company fundamentals | 6 hours |
| Quotes | Existing Phase 2 setting, 15 seconds |
| Candles | Existing Phase 2 setting, 5 minutes |

The complete response is not cached with a long TTL. No Phase 5 database table or migration is
required.

## API and limitations

```http
GET /api/v1/assets/AAPL/intelligence
GET /api/v1/assets/GLD/intelligence
GET /api/v1/assets/XAUUSD/intelligence
```

A partial response remains HTTP 200 and includes warnings and availability flags. Stale
observations remain available with `freshness.state == "STALE"` and a warning. Gold responses
always state: `Company fundamentals are not applicable to gold.`

Twelve Data currently provides instrument lookup and market observations in this repository.
Alpha Vantage maps company `OVERVIEW`, ETF `ETF_PROFILE`, and documented gold identifiers.
Actual endpoint availability, coverage, and freshness depend on the configured provider account.
Optional values remain `null`; production code never substitutes mock data. Forex is
future-ready at the provider boundary but is not implemented in Phase 5.

## Testing

```powershell
cd backend
python -m ruff check app tests
python -m mypy app
python -m pytest

cd ..\frontend
npm.cmd test
npm.cmd run lint
npm.cmd run type-check
npm.cmd run format:check
```
