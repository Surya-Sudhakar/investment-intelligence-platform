from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Interval(StrEnum):
    FIVE_MINUTES = "5min"
    FIFTEEN_MINUTES = "15min"
    ONE_HOUR = "1h"
    ONE_DAY = "1day"


class DataStatus(StrEnum):
    UNKNOWN = "UNKNOWN"
    DELAYED = "DELAYED"
    CACHED = "CACHED"
    END_OF_DAY = "END_OF_DAY"


class ProviderCapabilities(BaseModel):
    provider_name: str
    historical_candles: bool
    latest_quote: bool
    symbol_search: bool
    symbol_details: bool
    websocket_prices: bool = False
    bid_ask: bool = False
    market_status: bool = False
    delayed_flag: bool
    supported_intervals: list[Interval]
    supported_asset_classes: list[Literal["stock"]]
    maximum_candle_limit: int
    free_plan_limitations: list[str]
    rate_limit_description: str


class SymbolSearchResult(BaseModel):
    symbol: str
    name: str
    exchange: str | None = None
    currency: str | None = None
    country: str | None = None
    asset_type: Literal["stock"] = "stock"
    provider: str
    provider_symbol: str


class SymbolDetails(SymbolSearchResult):
    timezone: str | None = None
    market_open_time: str | None = None
    market_close_time: str | None = None


class Candle(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    symbol: str
    interval: Interval
    time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int | None
    is_complete: bool
    provider: str
    source_timestamp: datetime
    received_at: datetime
    data_status: DataStatus

    @model_validator(mode="after")
    def validate_market_values(self) -> "Candle":
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("OHLC prices must be positive")
        if self.high < max(self.open, self.close, self.low):
            raise ValueError("high is inconsistent with OHLC values")
        if self.low > min(self.open, self.close, self.high):
            raise ValueError("low is inconsistent with OHLC values")
        if self.volume is not None and self.volume < 0:
            raise ValueError("volume must not be negative")
        return self


class CandleResponseData(BaseModel):
    symbol: str
    interval: Interval
    candles: list[Candle]
    provider: str
    count: int
    received_count: int
    rejected_count: int
    requested_at: datetime
    source_timezone: str | None
    data_status: DataStatus
    cached: bool


class CandleResponse(BaseModel):
    data: CandleResponseData


class Quote(BaseModel):
    symbol: str
    price: Decimal
    bid: Decimal | None = None
    ask: Decimal | None = None
    spread: Decimal | None = None
    open: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None
    previous_close: Decimal | None = None
    change: Decimal | None = None
    change_percentage: Decimal | None = None
    volume: int | None = None
    timestamp: datetime
    received_at: datetime
    provider: str
    delayed: bool
    market_open: bool | None = None
    data_status: DataStatus
    age_seconds: int = Field(ge=0)
    cached: bool = False

    @model_validator(mode="after")
    def validate_quote(self) -> "Quote":
        if self.price <= 0:
            raise ValueError("price must be positive")
        for value in (self.bid, self.ask, self.open, self.high, self.low):
            if value is not None and value <= 0:
                raise ValueError("quote price fields must be positive")
        if self.volume is not None and self.volume < 0:
            raise ValueError("volume must not be negative")
        if self.bid is None or self.ask is None:
            self.spread = None
        return self


class ProviderHealth(BaseModel):
    provider: str
    configured: bool
    reachable: bool
    authenticated: bool
    latency_ms: float | None
    last_checked_at: datetime
    message: str


class MarketStatus(BaseModel):
    market_open: bool | None
    message: str


class ProviderCandleBatch(BaseModel):
    candles: list[Candle]
    received_count: int
    rejected_count: int
    source_timezone: str | None
