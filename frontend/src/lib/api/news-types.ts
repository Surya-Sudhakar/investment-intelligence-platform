export type NewsArticle = {
  id: string;
  title: string;
  summary: string;
  source: string;
  published_at: string;
  url: string;
  category: string;
  relevance_score: number;
  sentiment: string;
  confidence: number;
  freshness: { state: string; age_seconds: number | null };
};

export type NewsIntelligence = {
  symbol: string;
  asset_type: string;
  provider: string;
  articles: NewsArticle[];
  groups: Array<{
    id: string;
    title: string;
    summary: string;
    article_count: number;
    sources: string[];
    sentiment: string;
    confidence: number;
  }>;
  aggregate: {
    positive_count: number;
    neutral_count: number;
    negative_count: number;
    unknown_count: number;
    overall_sentiment: string;
    confidence: number;
    explanation: string;
  };
  summary: string;
  freshness: { state: string; age_seconds: number | null };
  generated_at: string;
  warnings: string[];
};
