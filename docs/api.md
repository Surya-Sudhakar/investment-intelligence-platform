# API reference

The local API base URL is `http://localhost:8000/api/v1`. All current endpoints are read-only.
Known errors use the standard `error` envelope and include a request ID.

| Method | Path | Response |
|---|---|---|
| GET | `/` | Backend status and version |
| GET | `/api/v1/health` | `HealthResponse` |
| GET | `/api/v1/ready` | `ReadyResponse` |
| GET | `/api/v1/market-data/provider` | `ProviderCapabilities` |
| GET | `/api/v1/market-data/health` | `ProviderHealth` |
| GET | `/api/v1/symbols/search?q=Apple&limit=10` | `SymbolSearchResult[]` |
| GET | `/api/v1/symbols/{symbol}` | `SymbolDetails` |
| GET | `/api/v1/market-data/{symbol}/quote` | `Quote` |
| GET | `/api/v1/market-data/{symbol}/candles?interval=1day&limit=20` | `CandleResponse` |
| GET | `/api/v1/intelligence/health` | `IntelligenceHealth` |
| GET | `/api/v1/intelligence/{symbol}` | `IntelligenceSnapshot` |
| GET | `/api/v1/assessments/health` | `AssessmentHealth` |
| GET | `/api/v1/assessments/{symbol}?interval=1day` | `TechnicalAssessment` |
| GET | `/api/v1/assets/{symbol}/intelligence` | `AssetIntelligenceResponse` |

## Daily technical assessment

```http
GET /api/v1/assessments/AAPL?interval=1day
```

The `interval` parameter defaults to `1day`. Any other value returns HTTP 422 with error code
`UNSUPPORTED_INTERVAL`. The response includes:

- `assessment`, `technical_score`, and `confidence_score`
- independent `risk.score`, `risk.level`, coverage, and risk components
- directional components and structured factors
- data-quality metadata
- `technical-v1`, snapshot timestamp, and generation timestamp

The endpoint uses one daily Phase 3 snapshot. It does not call a provider adapter directly and
does not persist the response.

## Request IDs and errors

Clients may supply `X-Request-ID`; the backend exposes it on the response. Example:

```json
{
  "error": {
    "code": "UNSUPPORTED_INTERVAL",
    "message": "Interval 1h is not supported.",
    "details": null,
    "request_id": "example-request-id"
  }
}
```

## Asset intelligence

`GET /api/v1/assets/{symbol}/intelligence` identifies the asset in the backend and returns the
common Phase 5 envelope with asset-specific `profile`, `metrics`, optional stock
`classification`, `warnings`, and `availability`. Public gold requests use `XAUUSD`.

Partial and stale results use HTTP 200 with explicit warnings. Unknown provider instrument
types return the standardized `UNSUPPORTED_ASSET` response.
