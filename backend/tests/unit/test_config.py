import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_development_defaults_are_valid() -> None:
    settings = Settings(_env_file=None)
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.debug is False


def test_production_rejects_placeholder_credentials() -> None:
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            database_url="postgresql+psycopg://app:change-me@db/app",
            _env_file=None,
        )
