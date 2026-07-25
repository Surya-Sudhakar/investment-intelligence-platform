import pytest

from app.core.exceptions import ProviderConfigurationError
from app.modules.market_data.provider import ProviderRegistry


class NamedProvider:
    name = "test"


def test_registry_selects_provider() -> None:
    registry = ProviderRegistry()
    registry.register(NamedProvider())  # type: ignore[arg-type]
    assert registry.get("test").name == "test"
    assert registry.names == ("test",)


def test_registry_rejects_missing_provider() -> None:
    with pytest.raises(ProviderConfigurationError):
        ProviderRegistry().get("missing")
