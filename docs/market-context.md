# Phase 7 market context

Phase 7 compares an asset with its surrounding market using deterministic daily-price rules.
It does not produce an investment recommendation and does not consume macroeconomic, currency,
interest-rate, central-bank, bond, geopolitical, or news inputs.

## Architecture

`MarketContextService` resolves the asset with `AssetIntelligenceService`, obtains comparison
references through the `MarketContextProvider` protocol, and loads normalized daily candles
through `MarketDataService`. This preserves provider neutrality and reuses the existing candle
and asset caches.

```text
GET /api/v1/assets/{symbol}/market-context
  -> MarketContextService
  -> AssetIntelligenceService.resolve_asset()
  -> MarketContextProvider.references()
  -> MarketDataService.candles()
  -> deterministic market-context-v1 calculation
```

No Phase 7 data is persisted.

## Response and availability

Every optional field is an availability object:

```json
{
  "status": "unavailable",
  "value": null,
  "reason": "The provider did not supply an authoritative primary market index."
}
```

Statuses are:

- `available`: the value is present and its reason describes its source or calculation.
- `unavailable`: the value cannot be obtained from current provider capabilities.
- `not_applicable`: the concept does not apply to the asset type.
- `planned_phase8`: the concept requires Phase 8 inputs and is deliberately not calculated.

An unsupported value is never replaced by zero, `NEUTRAL`, an assumed index, or fabricated
metadata. `overall_context` is also an availability object and remains unavailable when there
is insufficient directional evidence.

## Daily calculation

The methodology identifier is `market-context-v1`. It uses the latest 20 complete daily
observations and requires at least 15.

```text
return % = ((last close / first close) - 1) * 100
relative strength = asset return % - reference return %
```

Relative strength first normalizes candles to their canonical UTC daily comparison date,
deduplicates provider revisions deterministically, and intersects the asset and reference
dates. Both returns use the same aligned start and end dates. The response reports actual
overlap, aligned timestamps, requested lookback, minimum required observations and whether the
alignment was sufficient. Insufficient overlap produces structured unavailable data.

Performance and relative-strength classifications:

| Value | Classification |
|---:|---|
| at least 5.00 | `VERY_STRONG` |
| at least 2.50 | `STRONG` |
| at least 0.50 | `POSITIVE` |
| greater than -0.50 | `NEUTRAL` |
| greater than -2.50 | `WEAK` |
| otherwise | `VERY_WEAK` |

Available components map to numeric signals from -3 through +3. Missing components do not
contribute directionally and reduce coverage and confidence.

### Stock weights

- Market trend: 15%
- Sector trend: 20%
- Industry trend: 15%
- Asset versus market: 20%
- Asset versus sector: 20%
- Asset versus industry: 10%

US exchange comparisons may use `SPY` as a labelled market proxy. Recognized US sectors may
use labelled Select Sector SPDR ETFs. A proxy is never described as the authoritative index
or as the sector average. Industry context remains unavailable without a reliable provider
reference.

### Gold weights

- Gold trend: 35%
- Silver trend: 20%
- Gold versus silver: 20%
- Commodity-index trend: 15%
- Commodity alignment: 10%

The configured provider may compare `XAU/USD` with `XAG/USD`. Safe-haven demand is marked
`planned_phase8`; Phase 7 does not infer it from macro, USD, rates, news, or events. A commodity
index is unavailable unless a provider supplies a compatible daily series.

### ETF weights

- Benchmark trend: 35%
- ETF versus benchmark: 50%
- Fund-category trend: 15%

ETF category, allocations, and concentration remain descriptive. They are not directional
signals. An ETF benchmark is unavailable unless the provider supplies an authoritative
reference.

## Confidence

Confidence is independent from direction:

```text
coverage * 70 + freshness quality * 20 + sample quality * 10
```

Use of a proxy applies a five-point confidence reduction. Missing series, stale observations,
or insufficient samples reduce confidence without changing unavailable inputs into neutral
signals.

## Caching and freshness

- Final complete response: `MARKET_CONTEXT_CACHE_TTL_SECONDS`, default 300 seconds.
- Partial response: `MARKET_CONTEXT_PARTIAL_CACHE_TTL_SECONDS`, default 60 seconds.
- Underlying candles reuse the existing `MarketDataService` cache.
- Reference requests are concurrent and unique per reference name.

Daily observations up to four calendar days old are `CURRENT`, four to seven days are `RECENT`,
and older observations are `STALE`. The calendar-day allowance prevents normal weekends from
being classified as stale.

## Known limitations

- Daily context only; multi-timeframe analysis is out of scope.
- Reference coverage depends on provider plan and instrument support.
- Curated proxy coverage is currently limited to recognized US exchanges and sectors.
- Industry references and authoritative ETF benchmarks are not guessed.
- Currency-mismatched comparisons are not introduced.
- Safe-haven demand and all macroeconomic interpretation are reserved for Phase 8.
