from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    app_name: str = "AI Investment Intelligence Platform API"
    app_version: str = "0.1.0"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    frontend_origin: str = "http://localhost:3000"
    database_url: str = Field(
        default="postgresql+psycopg://app:change-me@localhost:5432/investment_intelligence"
    )
    log_level: str = "INFO"
    log_json: bool = False
    sql_echo: bool = False
    market_data_provider: Literal["alpha_vantage", "twelve_data"] = "alpha_vantage"
    market_data_api_key: str | None = None
    market_data_base_url: str = "https://www.alphavantage.co/query"
    market_data_timeout_seconds: float = 10.0
    market_data_max_retries: int = 2
    market_data_cache_enabled: bool = True
    market_data_symbol_cache_ttl_seconds: int = 3600
    market_data_candle_cache_ttl_seconds: int = 300
    market_data_quote_cache_ttl_seconds: int = 15
    market_data_default_candle_limit: int = 100
    market_data_max_candle_limit: int = 500
    intelligence_poll_interval_seconds: float = 30.0
    intelligence_live_threshold_seconds: int = 60
    intelligence_stale_threshold_seconds: int = 900
    intelligence_candle_lookback: int = 260

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.app_env == "production":
            if self.debug:
                raise ValueError("DEBUG must be false in production")
            if "change-me" in self.database_url:
                raise ValueError("DATABASE_URL must use production credentials")
            if "localhost" in self.frontend_origin:
                raise ValueError("FRONTEND_ORIGIN must be explicitly configured")
            if not self.market_data_api_key:
                raise ValueError("MARKET_DATA_API_KEY is required in production")
        if self.market_data_max_retries > 5:
            raise ValueError("MARKET_DATA_MAX_RETRIES must be at most 5")
        if self.market_data_default_candle_limit > self.market_data_max_candle_limit:
            raise ValueError("MARKET_DATA_DEFAULT_CANDLE_LIMIT must not exceed the maximum")
        if self.intelligence_live_threshold_seconds >= self.intelligence_stale_threshold_seconds:
            raise ValueError("Intelligence live threshold must be lower than stale threshold")
        if self.intelligence_poll_interval_seconds <= 0:
            raise ValueError("INTELLIGENCE_POLL_INTERVAL_SECONDS must be positive")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
