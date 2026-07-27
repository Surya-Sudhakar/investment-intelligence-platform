import re

from app.modules.news.schemas import NewsArticle


def concise_summary(article: NewsArticle) -> str:
    source = article.summary.strip() or article.title.strip()
    if not source:
        return "Insufficient information is available to summarize this article."
    sentence = re.split(r"(?<=[.!?])\s+", source)[0]
    sentence = sentence[:280].rstrip()
    return (
        f"{sentence} This matters to {article.asset_symbol} because the story was "
        f"classified as {article.category.value.lower().replace('_', ' ')} news."
    )


def asset_summary(articles: list[NewsArticle], symbol: str) -> str:
    if not articles:
        return "Insufficient recent information is available to summarize."
    lead = max(articles, key=lambda item: (item.relevance_score, item.published_at))
    return f"For {symbol}, the most relevant recent development is: {lead.summary}"
