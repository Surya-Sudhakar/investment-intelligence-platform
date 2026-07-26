from typing import Protocol

from app.modules.assets.schemas import AssetResolution, ProviderAssetData


class AssetDataProvider(Protocol):
    @property
    def name(self) -> str: ...

    async def resolve_asset(self, symbol: str) -> AssetResolution: ...

    async def get_asset_data(self, resolution: AssetResolution) -> ProviderAssetData: ...
