export type AssessmentFactor = {
  code: string;
  message: string;
};

export type ScoringComponent = {
  name: string;
  weight: number;
  available: boolean;
  raw_value: string | number | null;
  signal: number | null;
  weighted_contribution: number | null;
  explanation: string;
};

export type RiskComponent = {
  name: string;
  weight: number;
  available: boolean;
  raw_value: string | number | null;
  risk_value: number | null;
  weighted_contribution: number | null;
  explanation: string;
};

export type TechnicalAssessment = {
  symbol: string;
  interval: "1day";
  time_horizon: "SWING_POSITION";
  assessment:
    "STRONGLY_BULLISH" | "BULLISH" | "NEUTRAL" | "BEARISH" | "STRONGLY_BEARISH";
  technical_score: number;
  confidence_score: number;
  risk: {
    score: number;
    level: "LOW" | "MODERATE" | "ELEVATED" | "HIGH" | "EXTREME";
    data_coverage_percentage: number;
    components: RiskComponent[];
  };
  components: ScoringComponent[];
  supporting_factors: AssessmentFactor[];
  conflicting_factors: AssessmentFactor[];
  risk_factors: AssessmentFactor[];
  missing_data_factors: AssessmentFactor[];
  data_quality: {
    freshness_state: string;
    source_age_seconds: number | null;
    quote_data_status: string;
    quote_cached: boolean;
    market_status: string;
    available_directional_weight: number;
    eligible_directional_weight: number;
    input_coverage_percentage: number;
    issues: string[];
  };
  scoring_version: string;
  snapshot_timestamp: string;
  generated_at: string;
};
