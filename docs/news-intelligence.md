# Phase 6 News Intelligence

Phase 6 adds provider-neutral news retrieval, deterministic `news-v1` sentiment, duplicate
grouping, grounded extractive summaries, and asset-level sentiment for stocks, gold, and ETFs.
It does not generate recommendations or modify Phases 3–5.

The endpoint is `GET /api/v1/assets/{symbol}/news?limit=20`. Alpha Vantage
`NEWS_SENTIMENT` is the initial production adapter. News credentials are deliberately separate
from market-data credentials. Twelve Data press releases were evaluated but are not normalized
because their response lacks the canonical article URL required by the Phase 6 contract.

Sentiment counts configured positive and negative event phrases, weights title matches more
strongly, handles direct negation, and returns `UNKNOWN` below the relevance threshold. Overall
sentiment weights deduplicated articles by relevance and confidence. Summaries quote only
provider title/summary content and explicitly report insufficient information.

Successful results cache for 15 minutes; empty results cache for 5 minutes. Provider errors are
not cached. No database migration is used.
