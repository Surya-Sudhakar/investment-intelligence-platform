export type AssetType = "STOCK" | "GOLD" | "ETF" | "UNKNOWN";

export type AssetIntelligence = {
  symbol: string;
  display_name: string | null;
  asset_type: AssetType;
  exchange: string | null;
  currency: string | null;
  provider: string;
  source_timestamp: string | null;
  generated_at: string;
  freshness: {
    state: string;
    age_seconds: number | null;
    reason: string;
  } | null;
  profile: Record<string, unknown> | null;
  metrics: Record<string, unknown> | null;
  classification: Record<string, string> | null;
  warnings: string[];
  availability: {
    profile: boolean;
    metrics: boolean;
    fundamentals: boolean;
    holdings: boolean;
    allocations: boolean;
    technical_snapshot: boolean;
  };
};
