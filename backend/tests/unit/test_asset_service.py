import asyncio
from decimal import Decimal

import pytest

from app.core.config import Settings
from app.core.exceptions import UnsupportedAssetError
from app.modules.assets.schemas import (
    AssetResolution,
    AssetType,
    ProviderAssetData,
    StockMetrics,
    StockProfile,
)
from app.modules.assets.service import AssetIntelligenceService
from app.modules.market_data.cache import TTLCache


class FakeProvider:
    name = "test"

    def __init__(self, asset_type: AssetType = AssetType.STOCK) -> None:
        self.asset_type = asset_type
        self.resolve_calls = 0
        self.data_calls = 0

    async def resolve_asset(self, symbol: str) -> AssetResolution:
        self.resolve_calls += 1
        provider_symbol = "XAU/USD" if symbol == "XAUUSD" else symbol
        return AssetResolution(
            symbol=symbol,
            provider_symbol=provider_symbol,
            display_name="Test asset",
            asset_type=self.asset_type,
            currency="USD",
        )

    async def get_asset_data(self, resolution: AssetResolution) -> ProviderAssetData:
        self.data_calls += 1
        return ProviderAssetData(
            resolution=resolution,
            stock_profile=StockProfile(company_name="Test Inc.")
            if resolution.asset_type is AssetType.STOCK
            else None,
            stock_metrics=StockMetrics(pe_ratio=Decimal("20"))
            if resolution.asset_type is AssetType.STOCK
            else None,
        )


class FailingMarketData:
    async def quote(self, symbol: str):
        from app.core.exceptions import ProviderUnavailableError

        raise ProviderUnavailableError()


class FailingIntelligence:
    async def snapshot(self, symbol: str):
        from app.core.exceptions import ProviderUnavailableError

        raise ProviderUnavailableError()


def service(provider: FakeProvider) -> AssetIntelligenceService:
    return AssetIntelligenceService(
        provider,
        FailingMarketData(),  # type: ignore[arg-type]
        FailingIntelligence(),  # type: ignore[arg-type]
        TTLCache(),
        Settings(app_env="test"),
    )


def test_stock_partial_data_and_cache() -> None:
    provider = FakeProvider()
    target = service(provider)

    first = asyncio.run(target.get_intelligence("aapl"))
    second = asyncio.run(target.get_intelligence("AAPL"))

    assert first.asset_type is AssetType.STOCK
    assert first.metrics.pe_ratio == Decimal("20")  # type: ignore[union-attr]
    assert first.source_timestamp is None
    assert any("Current price" in warning for warning in first.warnings)
    assert provider.resolve_calls == 1
    assert provider.data_calls == 1
    assert second.symbol == "AAPL"


def test_gold_alias_has_no_company_fundamentals() -> None:
    result = asyncio.run(service(FakeProvider(AssetType.GOLD)).get_intelligence("XAU/USD"))

    assert result.symbol == "XAUUSD"
    assert result.classification is None
    assert result.profile.note == "Company fundamentals are not applicable to gold."  # type: ignore[union-attr]


def test_unknown_asset_is_rejected() -> None:
    with pytest.raises(UnsupportedAssetError):
        asyncio.run(service(FakeProvider(AssetType.UNKNOWN)).get_intelligence("XYZ"))
