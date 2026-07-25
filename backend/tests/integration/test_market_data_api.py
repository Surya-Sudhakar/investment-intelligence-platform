from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.core.exceptions import ProviderRateLimitError
from app.main import app
from app.modules.market_data.dependencies import get_market_data_service
from app.modules.market_data.schemas import (
    Candle,
    CandleResponse,
    CandleResponseData,
    DataStatus,
    Interval,
    ProviderCapabilities,
    ProviderHealth,
    Quote,
    SymbolDetails,
    SymbolSearchResult,
)


class FakeMarketDataService:
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name="fake",
            historical_candles=True,
            latest_quote=True,
            symbol_search=True,
            symbol_details=True,
            delayed_flag=True,
            supported_intervals=list(Interval),
            supported_asset_classes=["stock"],
            maximum_candle_limit=500,
            free_plan_limitations=[],
            rate_limit_description="test",
        )

    async def health(self) -> ProviderHealth:
        return ProviderHealth(
            provider="fake",
            configured=True,
            reachable=True,
            authenticated=True,
            latency_ms=1,
            last_checked_at=datetime.now(UTC),
            message="ok",
        )

    async def search_symbols(self, query: str, limit: int) -> list[SymbolSearchResult]:
        return [
            SymbolSearchResult(
                symbol="AAPL",
                name="Apple",
                provider="fake",
                provider_symbol="AAPL",
            )
        ][:limit]

    async def symbol_details(self, symbol: str) -> SymbolDetails:
        return SymbolDetails(
            symbol=symbol.upper(),
            name="Apple",
            provider="fake",
            provider_symbol=symbol.upper(),
        )

    async def candles(
        self,
        symbol: str,
        interval: Interval,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> CandleResponse:
        del start, end
        now = datetime.now(UTC)
        candle = Candle(
            symbol=symbol.upper(),
            interval=interval,
            time=now,
            open=Decimal("10"),
            high=Decimal("12"),
            low=Decimal("9"),
            close=Decimal("11"),
            volume=0,
            is_complete=True,
            provider="fake",
            source_timestamp=now,
            received_at=now,
            data_status=DataStatus.UNKNOWN,
        )
        return CandleResponse(
            data=CandleResponseData(
                symbol=symbol.upper(),
                interval=interval,
                candles=[candle][:limit],
                provider="fake",
                count=1,
                received_count=1,
                rejected_count=0,
                requested_at=now,
                source_timezone="UTC",
                data_status=DataStatus.UNKNOWN,
                cached=False,
            )
        )

    async def quote(self, symbol: str) -> Quote:
        now = datetime.now(UTC)
        return Quote(
            symbol=symbol.upper(),
            price=Decimal("11"),
            timestamp=now,
            received_at=now,
            provider="fake",
            delayed=True,
            data_status=DataStatus.DELAYED,
            age_seconds=0,
        )


def test_market_data_endpoints(client: TestClient) -> None:
    app.dependency_overrides[get_market_data_service] = lambda: FakeMarketDataService()
    try:
        assert client.get("/api/v1/market-data/provider").status_code == 200
        assert client.get("/api/v1/market-data/health").json()["reachable"] is True
        assert client.get("/api/v1/symbols/search?q=apple").json()[0]["symbol"] == "AAPL"
        assert client.get("/api/v1/symbols/AAPL").json()["name"] == "Apple"
        candle_response = client.get("/api/v1/market-data/AAPL/candles?interval=1day&limit=10")
        assert candle_response.status_code == 200
        assert candle_response.json()["data"]["count"] == 1
        quote_response = client.get("/api/v1/market-data/AAPL/quote")
        assert quote_response.status_code == 200
        assert quote_response.json()["delayed"] is True
    finally:
        app.dependency_overrides.pop(get_market_data_service, None)


def test_market_data_request_validation(client: TestClient) -> None:
    app.dependency_overrides[get_market_data_service] = lambda: FakeMarketDataService()
    try:
        assert client.get("/api/v1/symbols/search?q=").status_code == 422
        assert client.get("/api/v1/symbols/search?q=aa&limit=30").status_code == 422
        unsupported = client.get("/api/v1/market-data/AAPL/candles?interval=2h")
        assert unsupported.status_code == 422
        assert unsupported.json()["error"]["code"] == "UNSUPPORTED_INTERVAL"
        invalid_range = client.get(
            "/api/v1/market-data/AAPL/candles"
            "?interval=1day&start=2026-07-24T00:00:00Z&end=2026-07-23T00:00:00Z"
        )
        assert invalid_range.status_code == 422
    finally:
        app.dependency_overrides.pop(get_market_data_service, None)


def test_provider_errors_use_standard_envelope(client: TestClient) -> None:
    class RateLimitedService(FakeMarketDataService):
        async def quote(self, symbol: str) -> Quote:
            del symbol
            raise ProviderRateLimitError(30)

    app.dependency_overrides[get_market_data_service] = lambda: RateLimitedService()
    try:
        response = client.get(
            "/api/v1/market-data/AAPL/quote",
            headers={"X-Request-ID": "market-test"},
        )
        assert response.status_code == 429
        assert response.json()["error"] == {
            "code": "MARKET_PROVIDER_RATE_LIMITED",
            "message": "The market-data provider rate limit was reached.",
            "details": {"retry_after_seconds": 30},
            "request_id": "market-test",
        }
    finally:
        app.dependency_overrides.pop(get_market_data_service, None)
