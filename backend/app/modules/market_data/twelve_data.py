import logging
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import ValidationError

from app.core.exceptions import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderInvalidResponseError,
    ProviderRateLimitError,
    SymbolNotFoundError,
)
from app.modules.market_data.http_client import MarketDataHttpClient
from app.modules.market_data.schemas import (
    Candle,
    DataStatus,
    Interval,
    MarketStatus,
    ProviderCandleBatch,
    ProviderCapabilities,
    ProviderHealth,
    Quote,
    SymbolDetails,
    SymbolSearchResult,
)

logger = logging.getLogger(__name__)


class TwelveDataProvider:
    name = "twelve_data"

    def __init__(self, api_key: str | None, base_url: str, client: MarketDataHttpClient) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.client = client

    def _params(self, **values: str) -> dict[str, str]:
        if not self.api_key:
            raise ProviderConfigurationError()
        return {**values, "apikey": self.api_key}

    async def _request(self, endpoint: str, **params: str) -> dict[str, Any]:
        payload = await self.client.get_json(f"{self.base_url}/{endpoint}", self._params(**params))
        if str(payload.get("status", "")).lower() == "error":
            code = int(payload.get("code", 0) or 0)
            message = str(payload.get("message", "")).lower()
            if code == 429 or "limit" in message or "credits" in message:
                raise ProviderRateLimitError()
            if code in {401, 403} or "api key" in message:
                raise ProviderAuthenticationError()
            if code == 404 or "not found" in message:
                raise SymbolNotFoundError(str(params.get("symbol", "requested")))
            raise ProviderInvalidResponseError()
        return payload

    @staticmethod
    def _timestamp(raw: object) -> datetime:
        if isinstance(raw, (int, float)):
            return datetime.fromtimestamp(raw, UTC)
        parsed = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
        return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed.astimezone(UTC)

    @staticmethod
    def _optional_decimal(value: object) -> Decimal | None:
        if value is None or str(value).strip() == "":
            return None
        return Decimal(str(value))

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name=self.name,
            historical_candles=True,
            latest_quote=True,
            symbol_search=True,
            symbol_details=True,
            delayed_flag=False,
            supported_intervals=list(Interval),
            supported_asset_classes=["stock"],
            maximum_candle_limit=5000,
            free_plan_limitations=[
                "Basic service uses API credits per minute and per day.",
                "Exchange availability and real-time entitlements depend on the plan.",
            ],
            rate_limit_description="Basic plan: 8 API credits per minute and 800 per day.",
        )

    async def search_symbols(self, query: str, limit: int) -> list[SymbolSearchResult]:
        payload = await self._request("symbol_search", symbol=query, outputsize=str(limit))
        data = payload.get("data")
        if not isinstance(data, list):
            raise ProviderInvalidResponseError()
        results: list[SymbolSearchResult] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            asset_type = str(item.get("instrument_type", "")).lower()
            if asset_type not in {"common stock", "stock", "equity"}:
                continue
            symbol = str(item.get("symbol", "")).strip().upper()
            if symbol:
                results.append(
                    SymbolSearchResult(
                        symbol=symbol,
                        name=str(item.get("instrument_name") or symbol),
                        exchange=str(item.get("exchange") or "") or None,
                        currency=str(item.get("currency") or "") or None,
                        country=str(item.get("country") or "") or None,
                        provider=self.name,
                        provider_symbol=symbol,
                    )
                )
        return results[:limit]

    async def get_symbol_details(self, symbol: str) -> SymbolDetails:
        payload = await self._request("stocks", symbol=symbol)
        data = payload.get("data")
        if not isinstance(data, list) or not data or not isinstance(data[0], dict):
            raise SymbolNotFoundError(symbol)
        item = data[0]
        provider_symbol = str(item.get("symbol", symbol)).upper()
        return SymbolDetails(
            symbol=provider_symbol,
            name=str(item.get("name") or provider_symbol),
            exchange=str(item.get("exchange") or "") or None,
            currency=str(item.get("currency") or "") or None,
            country=str(item.get("country") or "") or None,
            provider=self.name,
            provider_symbol=provider_symbol,
            timezone=str(item.get("timezone") or "") or None,
        )

    async def get_candles(
        self,
        symbol: str,
        interval: Interval,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> ProviderCandleBatch:
        params = {
            "symbol": symbol,
            "interval": interval.value,
            "outputsize": str(limit),
            "timezone": "UTC",
            "order": "ASC",
        }
        if start:
            params["start_date"] = start.astimezone(UTC).isoformat()
        if end:
            params["end_date"] = end.astimezone(UTC).isoformat()
        payload = await self._request("time_series", **params)
        values = payload.get("values")
        if not isinstance(values, list):
            raise ProviderInvalidResponseError()
        raw_metadata = payload.get("meta")
        metadata: dict[str, object] = raw_metadata if isinstance(raw_metadata, dict) else {}
        received_at = datetime.now(UTC)
        candles: dict[datetime, Candle] = {}
        rejected = 0
        for row in values:
            try:
                if not isinstance(row, dict):
                    raise ValueError("row is not an object")
                timestamp = self._timestamp(row["datetime"])
                candles[timestamp] = Candle(
                    symbol=symbol,
                    interval=interval,
                    time=timestamp,
                    open=Decimal(str(row["open"])),
                    high=Decimal(str(row["high"])),
                    low=Decimal(str(row["low"])),
                    close=Decimal(str(row["close"])),
                    volume=int(row["volume"]) if row.get("volume") is not None else None,
                    is_complete=True,
                    provider=self.name,
                    source_timestamp=timestamp,
                    received_at=received_at,
                    data_status=DataStatus.END_OF_DAY
                    if interval is Interval.ONE_DAY
                    else DataStatus.UNKNOWN,
                )
            except (KeyError, ValueError, InvalidOperation, ValidationError) as exc:
                rejected += 1
                logger.warning(
                    "Rejected malformed Twelve Data candle",
                    extra={"error_type": type(exc).__name__},
                )
        return ProviderCandleBatch(
            candles=sorted(candles.values(), key=lambda candle: candle.time)[-limit:],
            received_count=len(values),
            rejected_count=rejected,
            source_timezone=str(metadata.get("exchange_timezone") or "UTC"),
        )

    async def get_quote(self, symbol: str) -> Quote:
        raw = await self._request("quote", symbol=symbol)
        try:
            timestamp = self._timestamp(raw.get("timestamp") or raw["datetime"])
            received_at = datetime.now(UTC)
            price = Decimal(str(raw.get("close") or raw["price"]))
            market_open = raw.get("is_market_open")
            return Quote(
                symbol=str(raw.get("symbol", symbol)).upper(),
                price=price,
                open=self._optional_decimal(raw.get("open")),
                high=self._optional_decimal(raw.get("high")),
                low=self._optional_decimal(raw.get("low")),
                previous_close=self._optional_decimal(raw.get("previous_close")),
                change=self._optional_decimal(raw.get("change")),
                change_percentage=self._optional_decimal(raw.get("percent_change")),
                volume=int(raw["volume"]) if raw.get("volume") is not None else None,
                timestamp=timestamp,
                received_at=received_at,
                provider=self.name,
                delayed=False,
                market_open=market_open if isinstance(market_open, bool) else None,
                data_status=DataStatus.UNKNOWN,
                age_seconds=max(0, int((received_at - timestamp).total_seconds())),
            )
        except (KeyError, ValueError, InvalidOperation, ValidationError) as exc:
            raise ProviderInvalidResponseError() from exc

    async def get_market_status(self, symbol: str | None = None) -> MarketStatus:
        if not symbol:
            return MarketStatus(market_open=None, message="A symbol is required.")
        quote = await self.get_quote(symbol)
        return MarketStatus(
            market_open=quote.market_open,
            message="Market status is derived from the Twelve Data quote.",
        )

    async def health_check(self) -> ProviderHealth:
        checked_at = datetime.now(UTC)
        if not self.api_key:
            return self._health(checked_at, 0, False, False, "API key is not configured.")
        started = time.perf_counter()
        try:
            await self._request("quote", symbol="AAPL")
        except ProviderAuthenticationError:
            return self._health(checked_at, started, False, False, "Authentication failed.")
        except Exception:
            return self._health(checked_at, started, True, False, "Provider is unavailable.")
        return self._health(checked_at, started, True, True, "Provider responded successfully.")

    def _health(
        self,
        checked_at: datetime,
        started: float,
        authenticated: bool,
        reachable: bool,
        message: str,
    ) -> ProviderHealth:
        latency = round((time.perf_counter() - started) * 1000, 2) if started else None
        return ProviderHealth(
            provider=self.name,
            configured=bool(self.api_key),
            reachable=reachable,
            authenticated=authenticated,
            latency_ms=latency,
            last_checked_at=checked_at,
            message=message,
        )

    async def stream_prices(self, symbols: list[str]) -> AsyncIterator[Quote]:
        del symbols
        raise NotImplementedError("Streaming is not implemented in Phase 3")
        yield  # pragma: no cover
