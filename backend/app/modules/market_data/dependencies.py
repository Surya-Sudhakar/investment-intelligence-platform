from typing import cast

from fastapi import Request

from app.modules.market_data.service import MarketDataService


def get_market_data_service(request: Request) -> MarketDataService:
    return cast(MarketDataService, request.app.state.market_data_service)
