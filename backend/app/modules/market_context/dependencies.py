from typing import cast

from fastapi import Request

from app.modules.market_context.service import MarketContextService


def get_market_context_service(request: Request) -> MarketContextService:
    return cast(MarketContextService, request.app.state.market_context_service)
