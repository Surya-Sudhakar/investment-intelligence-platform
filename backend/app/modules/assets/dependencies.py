from typing import cast

from fastapi import Request

from app.modules.assets.service import AssetIntelligenceService


def get_asset_intelligence_service(request: Request) -> AssetIntelligenceService:
    return cast(AssetIntelligenceService, request.app.state.asset_intelligence_service)
