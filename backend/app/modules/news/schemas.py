from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl

from app.modules.assets.schemas import AssetType


class NewsSentiment(StrEnum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"
    UNKNOWN = "UNKNOWN"


class NewsFreshness(StrEnum):
    FRESH = "FRESH"
    RECENT = "RECENT"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"


class NewsCategory(StrEnum):
    EARNINGS = "EARNINGS"
    PRODUCT = "PRODUCT"
    LEGAL = "LEGAL"
    ACQUISITION = "ACQUISITION"
    MANAGEMENT = "MANAGEMENT"
    REGULATORY = "REGULATORY"
    FUND = "FUND"
    INDEX = "INDEX"
    MONETARY_POLICY = "MONETARY_POLICY"
    INFLATION = "INFLATION"
    CURRENCY = "CURRENCY"
    GEOPOLITICAL = "GEOPOLITICAL"
    COMMODITY = "COMMODITY"
    OTHER = "OTHER"


class NewsFreshnessMetadata(BaseModel):
    state: NewsFreshness
    age_seconds: int | None
    evaluated_at: datetime


class ProviderNewsArticle(BaseModel):
    id: str
    title: str
    summary: str
    source: str
    published_at: datetime
    url: HttpUrl
    language: str | None = None
    provider: str
    relevance_score: int | None = Field(default=None, ge=0, le=100)


class NewsArticle(ProviderNewsArticle):
    asset_symbol: str
    asset_type: AssetType
    category: NewsCategory
    relevance_score: int = Field(ge=0, le=100)
    sentiment: NewsSentiment
    confidence: int = Field(ge=0, le=100)
    freshness: NewsFreshnessMetadata
    sentiment_factors: list[str] = Field(default_factory=list)


class GroupedNewsStory(BaseModel):
    id: str
    title: str
    summary: str
    article_count: int
    article_ids: list[str]
    sources: list[str]
    earliest_published_at: datetime
    latest_published_at: datetime
    sentiment: NewsSentiment
    confidence: int


class AssetNewsAggregate(BaseModel):
    positive_count: int
    neutral_count: int
    negative_count: int
    unknown_count: int
    overall_sentiment: NewsSentiment
    confidence: int
    explanation: str


class AssetNewsIntelligence(BaseModel):
    symbol: str
    asset_type: AssetType
    provider: str
    articles: list[NewsArticle]
    groups: list[GroupedNewsStory]
    aggregate: AssetNewsAggregate
    summary: str
    freshness: NewsFreshnessMetadata
    generated_at: datetime
    warnings: list[str] = Field(default_factory=list)
