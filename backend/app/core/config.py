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

    @model_validator(mode="after")
    def validate_production(self) -> "Settings":
        if self.app_env == "production":
            if self.debug:
                raise ValueError("DEBUG must be false in production")
            if "change-me" in self.database_url:
                raise ValueError("DATABASE_URL must use production credentials")
            if "localhost" in self.frontend_origin:
                raise ValueError("FRONTEND_ORIGIN must be explicitly configured")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
