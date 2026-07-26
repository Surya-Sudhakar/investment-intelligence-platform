from typing import cast

from fastapi import Request

from app.modules.intelligence.service import IntelligenceService


def get_intelligence_service(request: Request) -> IntelligenceService:
    return cast(IntelligenceService, request.app.state.intelligence_service)
