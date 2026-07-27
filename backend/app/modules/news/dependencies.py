from typing import cast

from fastapi import Request

from app.modules.news.service import NewsIntelligenceService


def get_news_service(request: Request) -> NewsIntelligenceService:
    return cast(NewsIntelligenceService, request.app.state.news_service)
