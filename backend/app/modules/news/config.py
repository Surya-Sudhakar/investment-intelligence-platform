from dataclasses import dataclass


@dataclass(frozen=True)
class NewsRules:
    version: str = "news-v1"
    positive: tuple[str, ...] = (
        "beats expectations",
        "record revenue",
        "raises guidance",
        "approved",
        "partnership",
        "acquisition",
        "fee reduction",
        "inflows",
        "safe-haven demand",
        "central bank buying",
        "dollar weakness",
    )
    negative: tuple[str, ...] = (
        "misses expectations",
        "lowers guidance",
        "investigation",
        "lawsuit",
        "recall",
        "resigns",
        "outflows",
        "index removal",
        "dollar strength",
    )
    minimum_relevance: int = 25


NEWS_V1 = NewsRules()
