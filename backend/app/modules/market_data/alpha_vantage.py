import logging
import time
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from datetime import time as datetime_time
from decimal import Decimal, InvalidOperation
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import ValidationError

from app.core.exceptions import (
    ProviderAuthenticationError,
    ProviderConfigurationError,
    ProviderInvalidResponseError,
    ProviderRateLimitError,
    SymbolNotFoundError,
)
from app.modules.assets.schemas import (
    AllocationItem,
    AssetResolution,
    AssetType,
    EtfMetrics,
    EtfProfile,
    GoldMetrics,
    ProviderAssetData,
    StockMetrics,
    StockProfile,
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
INTERVAL_MAP = {
    Interval.FIVE_MINUTES: "5min",
    Interval.FIFTEEN_MINUTES: "15min",
    Interval.ONE_HOUR: "60min",
}


class AlphaVantageProvider:
    name = "alpha_vantage"

    def __init__(self, api_key: str | None, base_url: str, client: MarketDataHttpClient) -> None:
        self.api_key = api_key
        self.base_url = base_url
        self.client = client

    def _params(self, **values: str) -> dict[str, str]:
        if not self.api_key:
            raise ProviderConfigurationError()
        return {**values, "apikey": self.api_key}

    @staticmethod
    def _check_provider_error(payload: dict[str, Any]) -> None:
        if "Note" in payload:
            raise ProviderRateLimitError()
        information = str(payload.get("Information", ""))
        if "rate limit" in information.lower() or "requests per day" in information.lower():
            raise ProviderRateLimitError()
        if "api key" in information.lower():
            raise ProviderAuthenticationError()
        if "Error Message" in payload:
            raise SymbolNotFoundError("requested")

    async def _request(self, **params: str) -> dict[str, Any]:
        payload = await self.client.get_json(self.base_url, self._params(**params))
        self._check_provider_error(payload)
        return payload

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            provider_name=self.name,
            historical_candles=True,
            latest_quote=True,
            symbol_search=True,
            symbol_details=True,
            delayed_flag=True,
            supported_intervals=list(Interval),
            supported_asset_classes=["stock"],
            maximum_candle_limit=500,
            free_plan_limitations=[
                "Free service is limited to 25 requests per day.",
                "Intraday endpoints and realtime/delayed entitlements may require premium access.",
                "Default GLOBAL_QUOTE data is updated at end of trading day.",
            ],
            rate_limit_description="Free API service: up to 25 requests per day.",
        )

    async def search_symbols(self, query: str, limit: int) -> list[SymbolSearchResult]:
        payload = await self._request(function="SYMBOL_SEARCH", keywords=query)
        matches = payload.get("bestMatches")
        if not isinstance(matches, list):
            raise ProviderInvalidResponseError()
        results: list[SymbolSearchResult] = []
        seen: set[str] = set()
        for item in matches:
            if not isinstance(item, dict) or item.get("3. type") != "Equity":
                continue
            symbol = str(item.get("1. symbol", "")).strip().upper()
            if not symbol or symbol in seen:
                continue
            seen.add(symbol)
            results.append(
                SymbolSearchResult(
                    symbol=symbol,
                    name=str(item.get("2. name", "")).strip(),
                    exchange=None,
                    currency=str(item.get("8. currency") or "").strip() or None,
                    country=str(item.get("4. region") or "").strip() or None,
                    provider=self.name,
                    provider_symbol=symbol,
                )
            )
            if len(results) >= limit:
                break
        return results

    async def get_symbol_details(self, symbol: str) -> SymbolDetails:
        payload = await self._request(function="OVERVIEW", symbol=symbol)
        if not payload or not payload.get("Symbol"):
            raise SymbolNotFoundError(symbol)
        asset_type = str(payload.get("AssetType", "")).lower()
        if asset_type and asset_type not in {"common stock", "stock", "equity"}:
            raise SymbolNotFoundError(symbol)
        return SymbolDetails(
            symbol=str(payload["Symbol"]).upper(),
            name=str(payload.get("Name", "")),
            exchange=str(payload.get("Exchange") or "") or None,
            currency=str(payload.get("Currency") or "") or None,
            country=str(payload.get("Country") or "") or None,
            provider=self.name,
            provider_symbol=str(payload["Symbol"]).upper(),
            timezone=None,
        )

    @staticmethod
    def _asset_decimal(value: object, *, percentage: bool = False) -> Decimal | None:
        if value is None or str(value).strip().casefold() in {"", "none", "-"}:
            return None
        try:
            parsed = Decimal(str(value).replace("%", "").replace(",", ""))
            return parsed * 100 if percentage and "%" not in str(value) else parsed
        except InvalidOperation:
            return None

    async def resolve_asset(self, symbol: str) -> AssetResolution:
        canonical = symbol.replace("/", "").replace("-", "").upper()
        if canonical == "XAUUSD":
            return AssetResolution(
                symbol="XAUUSD",
                provider_symbol="XAU",
                display_name="Gold Spot / US Dollar",
                asset_type=AssetType.GOLD,
                currency="USD",
            )
        payload = await self._request(function="OVERVIEW", symbol=symbol)
        if not payload or not payload.get("Symbol"):
            raise SymbolNotFoundError(symbol)
        raw_type = str(payload.get("AssetType", "")).casefold()
        asset_type = AssetType.ETF if "etf" in raw_type or "fund" in raw_type else AssetType.STOCK
        if raw_type and not any(value in raw_type for value in ("stock", "equity", "etf", "fund")):
            asset_type = AssetType.UNKNOWN
        return AssetResolution(
            symbol=str(payload["Symbol"]).upper(),
            provider_symbol=str(payload["Symbol"]).upper(),
            display_name=str(payload.get("Name") or symbol),
            asset_type=asset_type,
            exchange=str(payload.get("Exchange") or "") or None,
            currency=str(payload.get("Currency") or "") or None,
        )

    async def get_asset_data(self, resolution: AssetResolution) -> ProviderAssetData:
        if resolution.asset_type is AssetType.GOLD:
            payload = await self._request(function="GOLD_SILVER_SPOT", symbol="XAU")
            timestamp = payload.get("timestamp") or payload.get("last_updated")
            parsed_timestamp = None
            if timestamp:
                try:
                    parsed_timestamp = datetime.fromisoformat(
                        str(timestamp).replace("Z", "+00:00")
                    )
                except ValueError:
                    parsed_timestamp = None
            return ProviderAssetData(
                resolution=resolution,
                gold_metrics=GoldMetrics(
                    current_price=self._asset_decimal(
                        payload.get("price")
                        or payload.get("spot_price")
                        or payload.get("ask")
                        or payload.get("bid")
                    )
                ),
                source_timestamp=parsed_timestamp,
                warnings=[]
                if any(
                    payload.get(key) is not None
                    for key in ("price", "spot_price", "ask", "bid")
                )
                else ["The gold provider response did not include a normalized spot price."],
            )
        if resolution.asset_type is AssetType.ETF:
            payload = await self._request(function="ETF_PROFILE", symbol=resolution.provider_symbol)
            holdings = payload.get("holdings")
            sectors = payload.get("sectors")
            return ProviderAssetData(
                resolution=resolution,
                etf_profile=EtfProfile(
                    fund_name=resolution.display_name,
                    fund_provider=str(payload.get("provider") or "") or None,
                    fund_category=str(payload.get("assetClass") or "") or None,
                ),
                etf_metrics=EtfMetrics(
                    expense_ratio_percentage=self._asset_decimal(
                        payload.get("net_expense_ratio"), percentage=True
                    ),
                    net_assets=self._asset_decimal(payload.get("net_assets")),
                    holdings_count=len(holdings) if isinstance(holdings, list) else None,
                    top_holdings=[
                        AllocationItem(
                            name=str(item.get("description") or item.get("symbol") or "Unknown"),
                            weight_percentage=self._asset_decimal(
                                item.get("weight"), percentage=True
                            ),
                        )
                        for item in holdings[:10]
                        if isinstance(item, dict)
                    ]
                    if isinstance(holdings, list)
                    else None,
                    sector_allocation=[
                        AllocationItem(
                            name=str(item.get("sector") or "Unknown"),
                            weight_percentage=self._asset_decimal(
                                item.get("weight"), percentage=True
                            ),
                        )
                        for item in sectors
                        if isinstance(item, dict)
                    ]
                    if isinstance(sectors, list)
                    else None,
                ),
            )
        payload = await self._request(function="OVERVIEW", symbol=resolution.provider_symbol)
        return ProviderAssetData(
            resolution=resolution,
            stock_profile=StockProfile(
                company_name=str(payload.get("Name") or resolution.display_name),
                country=str(payload.get("Country") or "") or None,
                sector=str(payload.get("Sector") or "") or None,
                industry=str(payload.get("Industry") or "") or None,
            ),
            stock_metrics=StockMetrics(
                market_capitalization=self._asset_decimal(payload.get("MarketCapitalization")),
                pe_ratio=self._asset_decimal(payload.get("PERatio")),
                forward_pe_ratio=self._asset_decimal(payload.get("ForwardPE")),
                eps=self._asset_decimal(payload.get("EPS")),
                revenue=self._asset_decimal(payload.get("RevenueTTM")),
                revenue_growth_percentage=self._asset_decimal(
                    payload.get("QuarterlyRevenueGrowthYOY"), percentage=True
                ),
                profit_margin_percentage=self._asset_decimal(
                    payload.get("ProfitMargin"), percentage=True
                ),
                operating_margin_percentage=self._asset_decimal(
                    payload.get("OperatingMarginTTM"), percentage=True
                ),
                dividend_yield_percentage=self._asset_decimal(
                    payload.get("DividendYield"), percentage=True
                ),
                high_52_week=self._asset_decimal(payload.get("52WeekHigh")),
                low_52_week=self._asset_decimal(payload.get("52WeekLow")),
            ),
            warnings=[
                "Debt, cash, net income, and average volume are unavailable from this "
                "provider response."
            ],
        )

    @staticmethod
    def _timezone(value: str | None) -> ZoneInfo:
        try:
            return ZoneInfo(value or "UTC")
        except ZoneInfoNotFoundError:
            return ZoneInfo("UTC")

    async def get_candles(
        self,
        symbol: str,
        interval: Interval,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> ProviderCandleBatch:
        if interval is Interval.ONE_DAY:
            function = "TIME_SERIES_DAILY"
            params = {"function": function, "symbol": symbol, "outputsize": "compact"}
            series_key = "Time Series (Daily)"
        else:
            provider_interval = INTERVAL_MAP[interval]
            params = {
                "function": "TIME_SERIES_INTRADAY",
                "symbol": symbol,
                "interval": provider_interval,
                "outputsize": "compact",
            }
            series_key = f"Time Series ({provider_interval})"
        payload = await self._request(**params)
        metadata = payload.get("Meta Data")
        series = payload.get(series_key)
        if not isinstance(metadata, dict) or not isinstance(series, dict):
            raise ProviderInvalidResponseError()
        timezone_name = str(metadata.get("6. Time Zone") or metadata.get("5. Time Zone") or "UTC")
        timezone = self._timezone(timezone_name)
        received_at = datetime.now(UTC)
        candles: dict[datetime, Candle] = {}
        rejected = 0
        for raw_timestamp, row in series.items():
            try:
                if not isinstance(row, dict):
                    raise ValueError("row is not an object")
                parsed = datetime.fromisoformat(str(raw_timestamp)).replace(tzinfo=timezone)
                source_timestamp = parsed.astimezone(UTC)
                if start and source_timestamp < start:
                    continue
                if end and source_timestamp > end:
                    continue
                candle = Candle(
                    symbol=symbol,
                    interval=interval,
                    time=source_timestamp,
                    open=Decimal(str(row["1. open"])),
                    high=Decimal(str(row["2. high"])),
                    low=Decimal(str(row["3. low"])),
                    close=Decimal(str(row["4. close"])),
                    volume=int(row["5. volume"]) if row.get("5. volume") is not None else None,
                    is_complete=True,
                    provider=self.name,
                    source_timestamp=source_timestamp,
                    received_at=received_at,
                    data_status=DataStatus.END_OF_DAY
                    if interval is Interval.ONE_DAY
                    else DataStatus.UNKNOWN,
                )
                candles[source_timestamp] = candle
            except (KeyError, ValueError, InvalidOperation, ValidationError) as exc:
                rejected += 1
                logger.warning(
                    "Rejected malformed provider candle",
                    extra={"error_type": type(exc).__name__},
                )
        accepted = sorted(candles.values(), key=lambda item: item.time)[-limit:]
        return ProviderCandleBatch(
            candles=accepted,
            received_count=len(series),
            rejected_count=rejected,
            source_timezone=timezone_name,
        )

    async def get_quote(self, symbol: str) -> Quote:
        payload = await self._request(function="GLOBAL_QUOTE", symbol=symbol)
        raw = payload.get("Global Quote")
        if not isinstance(raw, dict) or not raw:
            raise SymbolNotFoundError(symbol)
        try:
            price = Decimal(str(raw["05. price"]))
            latest_day = date.fromisoformat(str(raw["07. latest trading day"]))
            source_timestamp = datetime.combine(latest_day, datetime_time.min, tzinfo=UTC)
            received_at = datetime.now(UTC)
            percentage = str(raw.get("10. change percent", "")).rstrip("%")
            return Quote(
                symbol=str(raw.get("01. symbol", symbol)).upper(),
                price=price,
                open=self._optional_decimal(raw.get("02. open")),
                high=self._optional_decimal(raw.get("03. high")),
                low=self._optional_decimal(raw.get("04. low")),
                volume=int(raw["06. volume"]) if raw.get("06. volume") else None,
                previous_close=self._optional_decimal(raw.get("08. previous close")),
                change=self._optional_decimal(raw.get("09. change")),
                change_percentage=self._optional_decimal(percentage),
                timestamp=source_timestamp,
                received_at=received_at,
                provider=self.name,
                delayed=True,
                market_open=None,
                data_status=DataStatus.END_OF_DAY,
                age_seconds=max(0, int((received_at - source_timestamp).total_seconds())),
            )
        except (KeyError, ValueError, InvalidOperation, ValidationError) as exc:
            raise ProviderInvalidResponseError() from exc

    @staticmethod
    def _optional_decimal(value: object) -> Decimal | None:
        if value is None or str(value).strip() == "":
            return None
        return Decimal(str(value))

    async def get_market_status(self, symbol: str | None = None) -> MarketStatus:
        del symbol
        return MarketStatus(
            market_open=None,
            message="Market status is not provided by the Phase 2 adapter.",
        )

    async def health_check(self) -> ProviderHealth:
        checked_at = datetime.now(UTC)
        if not self.api_key:
            return ProviderHealth(
                provider=self.name,
                configured=False,
                reachable=False,
                authenticated=False,
                latency_ms=None,
                last_checked_at=checked_at,
                message="Provider API key is not configured.",
            )
        started = time.perf_counter()
        try:
            await self._request(function="SYMBOL_SEARCH", keywords="IBM")
        except ProviderAuthenticationError:
            return self._health_failure(checked_at, started, False, "Authentication failed.")
        except Exception:
            return self._health_failure(checked_at, started, True, "Provider is unavailable.")
        return ProviderHealth(
            provider=self.name,
            configured=True,
            reachable=True,
            authenticated=True,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            last_checked_at=checked_at,
            message="Provider responded successfully.",
        )

    def _health_failure(
        self, checked_at: datetime, started: float, authenticated: bool, message: str
    ) -> ProviderHealth:
        return ProviderHealth(
            provider=self.name,
            configured=True,
            reachable=False,
            authenticated=authenticated,
            latency_ms=round((time.perf_counter() - started) * 1000, 2),
            last_checked_at=checked_at,
            message=message,
        )

    async def stream_prices(self, symbols: list[str]) -> AsyncIterator[Quote]:
        del symbols
        raise NotImplementedError("Streaming is not implemented in Phase 2")
        yield  # pragma: no cover
