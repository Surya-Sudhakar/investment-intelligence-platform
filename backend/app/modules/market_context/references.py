from app.modules.assets.schemas import AssetIntelligenceResponse, AssetResolution, AssetType
from app.modules.market_context.config import SECTOR_PROXIES
from app.modules.market_context.schemas import (
    ContextReference,
    ContextReferences,
    ReferenceKind,
)

US_EXCHANGES = {"NASDAQ", "NYSE", "NYSE ARCA", "NYSEARCA", "AMEX"}


class ConfiguredContextProvider:
    """Resolves explicit comparison instruments without claiming proxies are indices."""

    def references(
        self,
        resolution: AssetResolution,
        asset: AssetIntelligenceResponse | None,
    ) -> ContextReferences:
        if resolution.asset_type is AssetType.GOLD:
            return ContextReferences(
                silver=ContextReference(
                    symbol="XAG/USD",
                    name="Silver Spot / US Dollar",
                    kind=ReferenceKind.COMMODITY,
                )
            )
        if resolution.asset_type is AssetType.ETF:
            return ContextReferences()
        if resolution.asset_type is not AssetType.STOCK:
            return ContextReferences()

        market = None
        exchange = (resolution.exchange or "").upper()
        if exchange in US_EXCHANGES:
            market = ContextReference(
                symbol="SPY",
                name="SPDR S&P 500 ETF Trust",
                kind=ReferenceKind.MARKET_PROXY,
                is_proxy=True,
            )

        sector_reference = None
        profile = asset.profile if asset is not None else None
        sector = getattr(profile, "sector", None)
        configured = SECTOR_PROXIES.get(sector.casefold()) if sector else None
        if configured and exchange in US_EXCHANGES:
            sector_reference = ContextReference(
                symbol=configured[0],
                name=configured[1],
                kind=ReferenceKind.SECTOR_PROXY,
                is_proxy=True,
            )
        return ContextReferences(market=market, sector=sector_reference)
