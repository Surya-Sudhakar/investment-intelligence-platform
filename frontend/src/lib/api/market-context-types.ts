import type { AssetType } from "./asset-intelligence-types";

export type AvailabilityStatus =
  "available" | "unavailable" | "not_applicable" | "planned_phase8";

export type AvailableValue<T> = {
  status: AvailabilityStatus;
  value: T | null;
  reason: string;
  alignment?: {
    actual_overlap_count: number;
    aligned_start_timestamp: string | null;
    aligned_end_timestamp: string | null;
    requested_lookback: number;
    minimum_required: number;
    alignment_sufficient: boolean;
  } | null;
};

export type ContextClassification =
  "VERY_STRONG" | "STRONG" | "POSITIVE" | "NEUTRAL" | "WEAK" | "VERY_WEAK";

export type ContextReference = {
  symbol: string;
  name: string;
  kind: string;
  is_proxy: boolean;
};

export type PerformanceObservation = {
  reference: ContextReference;
  return_percentage: string;
  classification: ContextClassification;
  observations: number;
  first_timestamp: string;
  last_timestamp: string;
};

export type RelativeStrengthObservation = {
  asset_symbol: string;
  reference: ContextReference;
  difference_percentage_points: string;
  classification: ContextClassification;
  overlapping_observations: number;
};

export type MarketContext = {
  symbol: string;
  display_name: string;
  asset_type: AssetType;
  provider: string;
  methodology_version: string;
  horizon: { interval: "1day"; lookback_sessions: number };
  overall_context: AvailableValue<ContextClassification>;
  confidence: number;
  partial_data_status: "complete" | "partial" | "unavailable";
  market: Record<string, AvailableValue<unknown>>;
  sector: Record<string, AvailableValue<unknown>>;
  industry: Record<string, AvailableValue<unknown>>;
  commodity: Record<string, AvailableValue<unknown>>;
  etf: Record<string, AvailableValue<unknown>>;
  relative_strength: Record<string, AvailableValue<unknown>>;
  supporting_observations: string[];
  warnings: string[];
  freshness: {
    status: AvailabilityStatus;
    state: string | null;
    oldest_source_timestamp: string | null;
    newest_source_timestamp: string | null;
    age_days: number | null;
    reason: string;
  };
  availability: Record<string, AvailabilityStatus>;
  source_timestamp: AvailableValue<string>;
  generated_at: string;
};
