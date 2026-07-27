import hashlib
import re

from app.modules.news.schemas import GroupedNewsStory, NewsArticle, NewsSentiment


def _key(title: str) -> str:
    words = re.findall(r"[a-z0-9]+", title.casefold())
    return " ".join(word for word in words if word not in {"the", "a", "an", "and"})[:80]


def group_articles(articles: list[NewsArticle]) -> list[GroupedNewsStory]:
    buckets: dict[str, list[NewsArticle]] = {}
    for article in articles:
        buckets.setdefault(_key(article.title), []).append(article)
    groups = []
    for key, items in buckets.items():
        lead = max(items, key=lambda item: item.relevance_score)
        scores = [
            1
            if item.sentiment is NewsSentiment.POSITIVE
            else -1
            if item.sentiment is NewsSentiment.NEGATIVE
            else 0
            for item in items
        ]
        total = sum(scores)
        sentiment = (
            NewsSentiment.POSITIVE
            if total > 0
            else NewsSentiment.NEGATIVE
            if total < 0
            else NewsSentiment.NEUTRAL
        )
        groups.append(
            GroupedNewsStory(
                id=hashlib.sha256(key.encode()).hexdigest()[:16],
                title=lead.title,
                summary=lead.summary,
                article_count=len(items),
                article_ids=[item.id for item in items],
                sources=sorted({item.source for item in items}),
                earliest_published_at=min(item.published_at for item in items),
                latest_published_at=max(item.published_at for item in items),
                sentiment=sentiment,
                confidence=round(sum(item.confidence for item in items) / len(items)),
            )
        )
    return sorted(groups, key=lambda item: item.latest_published_at, reverse=True)
