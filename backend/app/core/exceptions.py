class AppException(Exception):
    def __init__(
        self, code: str, message: str, status_code: int, details: object | None = None
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class DatabaseUnavailableError(AppException):
    def __init__(self) -> None:
        super().__init__("DATABASE_UNAVAILABLE", "The service is temporarily unavailable.", 503)


class MarketDataError(AppException):
    pass


class ProviderAuthenticationError(MarketDataError):
    def __init__(self) -> None:
        super().__init__("MARKET_PROVIDER_AUTH_FAILED", "Market-data authentication failed.", 502)


class ProviderRateLimitError(MarketDataError):
    def __init__(self, retry_after: int | None = None) -> None:
        super().__init__(
            "MARKET_PROVIDER_RATE_LIMITED",
            "The market-data provider rate limit was reached.",
            429,
            {"retry_after_seconds": retry_after} if retry_after is not None else None,
        )


class ProviderTimeoutError(MarketDataError):
    def __init__(self) -> None:
        super().__init__("MARKET_PROVIDER_TIMEOUT", "The market-data provider timed out.", 504)


class ProviderUnavailableError(MarketDataError):
    def __init__(self) -> None:
        super().__init__(
            "MARKET_PROVIDER_UNAVAILABLE",
            "The market-data provider is temporarily unavailable.",
            503,
        )


class ProviderInvalidResponseError(MarketDataError):
    def __init__(self) -> None:
        super().__init__(
            "MARKET_PROVIDER_INVALID_RESPONSE",
            "The market-data provider returned an invalid response.",
            502,
        )


class SymbolNotFoundError(MarketDataError):
    def __init__(self, symbol: str) -> None:
        super().__init__("SYMBOL_NOT_FOUND", f"Symbol {symbol} was not found.", 404)


class InvalidSymbolError(MarketDataError):
    def __init__(self) -> None:
        super().__init__("INVALID_SYMBOL", "The stock symbol is invalid.", 422)


class UnsupportedAssetError(MarketDataError):
    def __init__(self, symbol: str) -> None:
        super().__init__(
            "UNSUPPORTED_ASSET",
            f"The asset type for {symbol} could not be identified or is not supported.",
            422,
            {"symbol": symbol, "supported_asset_types": ["STOCK", "GOLD", "ETF"]},
        )


class UnsupportedIntervalError(MarketDataError):
    def __init__(self, interval: str) -> None:
        super().__init__("UNSUPPORTED_INTERVAL", f"Interval {interval} is not supported.", 422)


class ProviderConfigurationError(MarketDataError):
    def __init__(self) -> None:
        super().__init__(
            "MARKET_DATA_CONFIGURATION_ERROR",
            "Market-data provider configuration is incomplete.",
            503,
        )


class NewsProviderConfigurationError(MarketDataError):
    def __init__(self) -> None:
        super().__init__(
            "NEWS_PROVIDER_CONFIGURATION_ERROR",
            "News provider configuration is incomplete.",
            503,
        )
