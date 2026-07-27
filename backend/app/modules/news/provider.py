from typing import Protocol

from app.modules.assets.schemas import AssetResolution
from app.modules.news.schemas import ProviderNewsArticle


class NewsProvider(Protocol):
    @property
    def name(self) -> str: ...

    async def fetch_news(
        self, resolution: AssetResolution, limit: int
    ) -> list[ProviderNewsArticle]: ...
