import re

from app.modules.assets.schemas import AssetType
from app.modules.news.config import NEWS_V1
from app.modules.news.schemas import NewsCategory, NewsSentiment, ProviderNewsArticle

CATEGORIES = {
    NewsCategory.EARNINGS: ("earnings", "revenue", "guidance"),
    NewsCategory.PRODUCT: ("launch", "product", "recall"),
    NewsCategory.LEGAL: ("lawsuit", "legal", "court"),
    NewsCategory.ACQUISITION: ("acquisition", "merger", "acquire"),
    NewsCategory.MANAGEMENT: ("chief executive", "ceo", "resigns"),
    NewsCategory.REGULATORY: ("regulator", "approved", "investigation"),
    NewsCategory.FUND: ("fund", "inflows", "outflows", "expense ratio"),
    NewsCategory.INDEX: ("index addition", "index removal", "rebalance"),
    NewsCategory.MONETARY_POLICY: ("federal reserve", "interest rate", "monetary"),
    NewsCategory.INFLATION: ("inflation", "consumer prices"),
    NewsCategory.CURRENCY: ("dollar", "usd", "currency"),
    NewsCategory.GEOPOLITICAL: ("war", "conflict", "sanctions"),
    NewsCategory.COMMODITY: ("gold", "bullion", "commodity", "xau"),
}


def classify_category(text: str, asset_type: AssetType) -> NewsCategory:
    lowered = text.casefold()
    for category, phrases in CATEGORIES.items():
        if any(phrase in lowered for phrase in phrases):
            return category
    return NewsCategory.FUND if asset_type is AssetType.ETF else NewsCategory.OTHER


def classify_sentiment(article: ProviderNewsArticle) -> tuple[NewsSentiment, int, list[str]]:
    relevance = article.relevance_score or 50
    if relevance < NEWS_V1.minimum_relevance:
        return NewsSentiment.UNKNOWN, 0, ["Article relevance is below the threshold."]
    title = article.title.casefold()
    body = f"{article.title}. {article.summary}".casefold()
    score = 0
    factors: list[str] = []
    for phrase in NEWS_V1.positive:
        if phrase in body and not re.search(rf"\b(?:not|denied)\s+{re.escape(phrase)}", body):
            points = 2 if phrase in title else 1
            score += points
            factors.append(f"Positive phrase: {phrase}.")
    for phrase in NEWS_V1.negative:
        if phrase in body:
            points = 2 if phrase in title else 1
            score -= points
            factors.append(f"Negative phrase: {phrase}.")
    sentiment = (
        NewsSentiment.POSITIVE
        if score >= 2
        else NewsSentiment.NEGATIVE
        if score <= -2
        else NewsSentiment.NEUTRAL
    )
    confidence = min(100, 35 + abs(score) * 15 + relevance // 4)
    if not factors:
        confidence = min(55, relevance)
        factors.append("No strong directional phrases were detected.")
    return sentiment, confidence, factors
