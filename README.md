# AI Investment Intelligence Platform

## Project overview

This repository contains a modular investment-intelligence application built with FastAPI,
Next.js, PostgreSQL, and Docker Compose. It normalizes market data, derives deterministic
technical intelligence, and produces an explainable daily technical assessment.

This is a deterministic technical decision-support platform. It is not a broker, an automated
trading system, or a guaranteed prediction system. Technical assessments are not investment
recommendations.

## Current development status

Phases 1, 2, 3, 4A, 5, 6, and 7 are implemented. The application supports provider-neutral
stock, gold, and ETF intelligence; deterministic technical assessments; grounded news
intelligence; and surrounding-market context. Twelve Data is the configured default market-data
provider, while Alpha Vantage remains available as an alternative market-data adapter and as the
Phase 6 news provider.

### Phase 1 — Foundation

- FastAPI backend and Next.js frontend
- PostgreSQL, SQLAlchemy, and Alembic
- Docker Compose local environment
- Health and readiness endpoints
- Typed environment configuration
- Structured logging, request IDs, safe errors, and CORS
- Backend and frontend testing infrastructure

### Phase 2 — Market Data

- Provider-neutral `MarketDataProvider` contract
- Twelve Data and Alpha Vantage adapters
- Normalized symbol search, symbol details, quotes, and candles
- Supported market-data intervals: `5min`, `15min`, `1h`, and `1day`
- Provider capabilities and health reporting
- Timeout, bounded retry, validation, error mapping, and in-process TTL caching

### Phase 3 — Market Intelligence

- Freshness and exchange-status classification
- UTC candle aggregation and asynchronous quote polling support
- EMA20, EMA50, RSI14, ATR14, average volume, and 52-week range
- Previous close, daily change, and opening gap
- Trend, momentum, and volatility classifications
- Support, resistance, distance-to-level, and breakout-proximity observations
- Normalized `IntelligenceSnapshot` output and frontend dashboard

### Phase 4A — Technical Decision Support

- Daily-only deterministic technical assessments
- Five technical-outlook classifications
- Technical score from 0 to 100
- Separate confidence score from 0 to 100
- Independent risk score and risk level
- Component scoring breakdown and structured explanations
- Supporting, conflicting, risk, and missing-data factors
- Data-quality metadata and snapshot/generation timestamps
- Immutable, versioned `technical-v1` configuration
- Phase 4A frontend dashboard

### Phase 5 — Asset Intelligence

- Backend identification of `STOCK`, `GOLD`, `ETF`, and `UNKNOWN`
- Provider-neutral company, commodity, and fund profiles
- Versioned deterministic `fundamentals-v1` stock condition labels
- Partial-data, availability, warning, and freshness information
- Gold observations without fabricated company fundamentals
- Optional ETF holdings and allocations when supported

Phase 5 does not combine fundamentals with the Phase 4A technical score. See
[docs/asset-intelligence.md](docs/asset-intelligence.md).

### Phase 6 — News Intelligence

- Provider-neutral news-provider contract with an Alpha Vantage adapter
- Asset-scoped article retrieval, validation, grouping, and bounded caching
- Deterministic sentiment classification and confidence metadata
- Grounded summaries derived from returned article data
- Freshness, warnings, partial-data handling, and frontend dashboard

See [docs/news-intelligence.md](docs/news-intelligence.md).

### Phase 7 — Market Context

- Provider-neutral context for stocks, gold, and ETFs
- Deterministic `market-context-v1` classifications and confidence
- Market, sector, industry, commodity, benchmark, and relative-strength observations
- Shared-date alignment for every comparative return calculation
- Structured availability, freshness, warnings, proxy labels, and partial-data status
- Frontend Market Context dashboard

Phase 7 does not include macroeconomic analysis. See
[docs/market-context.md](docs/market-context.md).

The public assessment endpoint supports only `interval=1day`. `AssessmentService` calls
`IntelligenceService.snapshot()` once per request. It has no direct provider dependency and does
not persist assessments to PostgreSQL.

## Architecture overview

```text
Next.js frontend
  → FastAPI Assessment API
  → AssessmentService
  → IntelligenceService
  → MarketDataService / in-process cache
  → Twelve Data or the configured provider
```

The backend is a modular monolith. API routes remain thin, while provider integration,
intelligence generation, and assessment scoring live in separate modules. See
[docs/architecture.md](docs/architecture.md), [docs/market-data.md](docs/market-data.md),
[docs/intelligence.md](docs/intelligence.md), and
[docs/technical-assessments.md](docs/technical-assessments.md).

## Repository structure

```text
backend/
  app/api/v1/routes/             FastAPI route modules
  app/core/                      Configuration, logging, and application errors
  app/db/                        SQLAlchemy session and models
  app/modules/market_data/       Provider adapters, normalized schemas, cache, and service
  app/modules/intelligence/      Indicators, classifications, polling, and snapshots
  app/modules/assessments/       technical-v1 configuration, scoring, schemas, and service
  app/modules/assets/            Asset classification, profiles, and fundamentals
  migrations/                    Alembic migrations
  tests/unit/                    Backend unit tests
  tests/integration/             Backend API and migration tests

frontend/
  src/app/                       Next.js App Router entry points
  src/components/                Status, market-data, intelligence, and assessment screens
  src/hooks/                     React Query hooks
  src/lib/api/                   Typed API clients and response types
  src/lib/config/                Public environment validation
  tests/                         Vitest and Testing Library tests

docs/                            Architecture and capability documentation
scripts/                         PowerShell quality-command helpers
.github/workflows/               Continuous integration
docker-compose.yml               Local application services
```

## Local Docker setup

Prerequisites are Docker Desktop with Compose and available ports 3000 and 8000.

```powershell
Copy-Item .env.example .env
# Put the real provider key only in .env.
docker compose up --build -d postgres
docker compose run --rm backend alembic upgrade head
docker compose up --build -d backend frontend
docker compose ps
```

Open [http://localhost:3000](http://localhost:3000). The API is available at
`http://localhost:8000`, and interactive API documentation is at
`http://localhost:8000/docs`.

PostgreSQL is intentionally not published on a host port. The frontend image does not use a
Windows source bind mount, so rebuild it after frontend source changes.

Useful commands:

```powershell
docker compose logs -f backend frontend
docker compose exec backend pytest
docker compose down
```

## Non-Docker setup

Install Python 3.12+, Node.js 22+, npm, and PostgreSQL 17. Create the local database and configure
`backend/.env` from the example.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

In a second terminal:

```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```

## Environment variables

Never commit `.env`, `.env.local`, API keys, database credentials, or other secret values.
Example files contain placeholders only.

| Area | Variables |
|---|---|
| Application | `APP_NAME`, `APP_VERSION`, `APP_ENV`, `DEBUG`, `API_V1_PREFIX` |
| Backend server | `BACKEND_HOST`, `BACKEND_PORT`, `FRONTEND_ORIGIN` |
| Database | `DATABASE_URL`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `SQL_ECHO` |
| Logging | `LOG_LEVEL`, `LOG_JSON` |
| Provider | `MARKET_DATA_PROVIDER`, `MARKET_DATA_API_KEY`, `MARKET_DATA_BASE_URL` |
| Provider resilience | `MARKET_DATA_TIMEOUT_SECONDS`, `MARKET_DATA_MAX_RETRIES` |
| Cache | `MARKET_DATA_CACHE_ENABLED`, `MARKET_DATA_SYMBOL_CACHE_TTL_SECONDS`, `MARKET_DATA_CANDLE_CACHE_TTL_SECONDS`, `MARKET_DATA_QUOTE_CACHE_TTL_SECONDS` |
| Candle limits | `MARKET_DATA_DEFAULT_CANDLE_LIMIT`, `MARKET_DATA_MAX_CANDLE_LIMIT` |
| Intelligence | `INTELLIGENCE_POLL_INTERVAL_SECONDS`, `INTELLIGENCE_LIVE_THRESHOLD_SECONDS`, `INTELLIGENCE_STALE_THRESHOLD_SECONDS`, `INTELLIGENCE_CANDLE_LOOKBACK` |
| Frontend | `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_APP_ENV` |

Only variables prefixed with `NEXT_PUBLIC_` are exposed to the browser. Never place a provider
key in one of those variables.

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Backend process information |
| GET | `/api/v1/health` | Application liveness and version |
| GET | `/api/v1/ready` | Initialization and database readiness |
| GET | `/api/v1/market-data/provider` | Provider capabilities and limitations |
| GET | `/api/v1/market-data/health` | Provider configuration and connectivity |
| GET | `/api/v1/symbols/search?q=Apple&limit=10` | Search stock symbols |
| GET | `/api/v1/symbols/AAPL` | Normalized symbol details |
| GET | `/api/v1/market-data/AAPL/quote` | Normalized quote |
| GET | `/api/v1/market-data/AAPL/candles?interval=1day&limit=20` | Normalized candles |
| GET | `/api/v1/intelligence/health` | Intelligence-service readiness |
| GET | `/api/v1/intelligence/AAPL` | Daily Phase 3 intelligence snapshot |
| GET | `/api/v1/assessments/health` | Assessment input readiness and scoring version |
| GET | `/api/v1/assessments/AAPL?interval=1day` | Daily technical assessment |
| GET | `/api/v1/assets/AAPL/intelligence` | Stock, gold, or ETF asset intelligence |
| GET | `/api/v1/assets/AAPL/news?limit=20` | News intelligence and sentiment |
| GET | `/api/v1/assets/AAPL/market-context` | Stock, gold, or ETF surrounding-market context |

Errors use the standard envelope:

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

## Technical-assessment example

Request:

```http
GET /api/v1/assessments/AAPL?interval=1day
```

Illustrative response — these are example values, not live market data:

```json
{
  "symbol": "AAPL",
  "interval": "1day",
  "time_horizon": "SWING_POSITION",
  "assessment": "BULLISH",
  "technical_score": 72,
  "confidence_score": 86,
  "risk": {
    "score": 43,
    "level": "ELEVATED",
    "data_coverage_percentage": 100,
    "components": []
  },
  "components": [
    {
      "name": "trend",
      "weight": 20,
      "available": true,
      "raw_value": "UPTREND",
      "signal": 0.6,
      "weighted_contribution": 12,
      "explanation": "The Phase 3 trend classification is UPTREND."
    }
  ],
  "supporting_factors": [],
  "conflicting_factors": [],
  "risk_factors": [],
  "missing_data_factors": [],
  "data_quality": {
    "freshness_state": "DELAYED",
    "source_age_seconds": 60,
    "quote_data_status": "DELAYED",
    "quote_cached": false,
    "market_status": "OPEN",
    "available_directional_weight": 100,
    "eligible_directional_weight": 100,
    "input_coverage_percentage": 100,
    "issues": []
  },
  "scoring_version": "technical-v1",
  "snapshot_timestamp": "2026-07-25T12:00:00Z",
  "generated_at": "2026-07-25T12:00:01Z"
}
```

### Score interpretation

- **Technical score** measures directional technical evidence from the available Phase 3 fields.
- **Confidence score** measures coverage, freshness, and agreement. Missing or stale inputs reduce
  confidence without inventing replacement values.
- **Risk score** is calculated independently from volatility, freshness, level distances,
  price-move magnitude, range extremes, and market status.

Supported technical outlooks are:

- `STRONGLY_BULLISH`
- `BULLISH`
- `NEUTRAL`
- `BEARISH`
- `STRONGLY_BEARISH`

RSI overbought and oversold values express directional momentum together with extension risk;
they are not automatic reversal conditions.

## Testing and quality

```powershell
cd backend
python -m ruff format --check app tests
python -m ruff check app tests --no-cache
python -m mypy app
python -m pytest -q -p no:cacheprovider

cd ..\frontend
npm run format:check
npm run lint
npm run type-check
npm test
npm run build

cd ..
git diff --check
```

Verified status for the Phase 6/7 baseline:

- Backend: 78 tests passed
- Frontend: 18 tests passed
- Alembic upgrade, downgrade, and clean re-upgrade: passed
- Production frontend build: passed
- Ruff formatting, Ruff lint, strict MyPy, ESLint, TypeScript, and Prettier: passed
- `git diff --check`: passed
- GitHub Actions CI run `#20`: passed

## Current limitations

- Phase 7 Market Context uses deterministic 20-session daily comparisons for stocks, gold,
  and ETFs. Unsupported data is represented with structured availability metadata.
- Phase 7 does not calculate interest-rate, inflation, central-bank, currency, bond,
  geopolitical, or other macroeconomic context; those inputs are reserved for Phase 8.

- Phase 4A supports daily assessments only.
- No authentication, portfolios, watchlists, position sizing, or execution.
- No machine learning, LLM-generated reasoning, prediction engine, or macro-intelligence engine.
- Phase 5 fundamentals, Phase 6 news sentiment, and Phase 7 market context remain independent;
  they are not combined into an investment recommendation.
- No Redis, Celery, WebSockets, or distributed cache.
- Assessments are computed on request and are not stored in PostgreSQL.
- Provider quotas and entitlements can limit freshness and intraday market-data access.
- The in-process cache is local to each backend instance.

## Future roadmap

- Make Phase 3 snapshots explicitly interval-aware before considering intraday assessments.
- Add Phase 8 macro intelligence as a separately reviewed module.
- Expand Phase 5–7 provider coverage without changing their provider-neutral contracts.
- Add authentication, portfolios, and watchlists with explicit security and persistence designs.
- Consider shared caching and background processing when operational requirements justify them.
- Expand observability, deployment automation, and production hardening.
