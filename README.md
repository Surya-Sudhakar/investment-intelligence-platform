<<<<<<< HEAD
# AI Investment Intelligence Platform

Phase 1 establishes a stable local development foundation for a future stock-market
decision-support application. It is not a broker, automated trading system, leveraged trading
system, or guaranteed prediction system.

## Scope

Included: FastAPI, Next.js, PostgreSQL, SQLAlchemy, Alembic, typed environment configuration,
structured logs, safe errors, request IDs, health/readiness checks, a development status page,
tests, Docker Compose, and CI.

Deliberately absent: market data, indicators, recommendations, trade setups, position sizing,
authentication, portfolios, watchlists, practice trades, polished dashboards, Redis, queues,
microservices, and cloud infrastructure.

## Stack and prerequisites

- Python 3.12+
- Node.js 22+ and npm
- Docker Engine with Docker Compose (recommended)
- PostgreSQL 17 for non-Docker development

## Repository

```text
backend/             FastAPI application, Alembic, and Python tests
frontend/            Next.js application and component tests
infrastructure/      infrastructure scope notes
docs/architecture.md architecture decisions and flows
scripts/             PowerShell quality-command wrappers
.github/workflows/   continuous integration
docker-compose.yml   local three-service environment
```

## Docker setup

```bash
cp .env.example .env
docker compose up --build -d postgres
docker compose run --rm backend alembic upgrade head
docker compose up --build
```

Open `http://localhost:3000`. The API is at `http://localhost:8000`.

```bash
docker compose logs -f
docker compose exec backend pytest
docker compose exec backend alembic current
docker compose down
```

To reset only the disposable development database (this permanently removes its local data):

```bash
docker compose down
docker volume rm ai-investment-intelligence_postgres_data
docker compose up --build -d postgres
docker compose run --rm backend alembic upgrade head
```

Confirm the volume name with `docker volume ls` before removal.

## Non-Docker setup

Create a PostgreSQL database and copy `backend/.env.example` to `backend/.env`, updating
`DATABASE_URL`. Then:

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

In a second terminal:

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

## Quality and tests

```bash
cd backend
ruff format --check .
ruff check .
mypy app
pytest

cd ../frontend
npm run format:check
npm run lint
npm run type-check
npm test
npm run build
```

Use `ruff format .` and `npm run format` to apply formatting. PowerShell users can also use
`scripts/backend.ps1` and `scripts/frontend.ps1`.

## Migrations

```bash
cd backend
alembic upgrade head
alembic current
alembic downgrade -1
alembic revision --autogenerate -m "describe change"
```

The initial reversible migration creates only `system_metadata` with UTC-aware timestamps.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Confirms the backend process is running |
| GET | `/api/v1/health` | Application liveness and version |
| GET | `/api/v1/ready` | Application initialization and database connectivity |

Errors use `{ "error": { "code", "message", "details", "request_id" } }`. Requests may supply
`X-Request-ID`; every response exposes it.

## Troubleshooting

- `ready` returns 503: verify PostgreSQL is healthy, credentials match, and migrations ran.
- Browser shows backend unavailable: verify port 8000 and `NEXT_PUBLIC_API_BASE_URL`.
- CORS failure: make `FRONTEND_ORIGIN` exactly match the browser origin.
- Changed database credentials after first startup: reset the development volume or restore the
  original values; PostgreSQL initialization variables apply only to a new volume.
- PowerShell blocks `npm.ps1`: run `npm.cmd` or use Command Prompt.

## Environment variables

Backend: `APP_NAME`, `APP_VERSION`, `APP_ENV`, `DEBUG`, `API_V1_PREFIX`, `BACKEND_HOST`,
`BACKEND_PORT`, `FRONTEND_ORIGIN`, `DATABASE_URL`, `LOG_LEVEL`, `LOG_JSON`, `SQL_ECHO`.

Frontend (public): `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_APP_ENV`.

PostgreSQL/Compose: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`.

## Next phase

The next planned phase may establish the first explicitly approved domain capability and its data
contracts. No Phase 2 functionality is present in this repository.

=======
# investment-intelligence-platform
>>>>>>> origin/main
