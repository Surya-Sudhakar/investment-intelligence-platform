from typing import Protocol

from app.modules.assets.schemas import AssetIntelligenceResponse, AssetResolution
from app.modules.market_context.schemas import ContextReferences


class MarketContextProvider(Protocol):
    def references(
        self,
        resolution: AssetResolution,
        asset: AssetIntelligenceResponse | None,
    ) -> ContextReferences: ...
