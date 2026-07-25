import type { Quote } from "./market-data-types";

export type IntelligenceSnapshot = {
  symbol: string;
  quote: Quote;
  freshness: {
    state: string;
    age_seconds: number | null;
    reason: string;
  };
  market_status: {
    state: string;
    exchange_timezone: string | null;
    reason: string;
  };
  trend: string;
  momentum: string;
  volatility: string;
  indicators: {
    ema20: string | null;
    ema50: string | null;
    rsi14: string | null;
    atr14: string | null;
    average_volume: string | null;
    high_52_week: string | null;
    low_52_week: string | null;
    daily_change_percentage: string | null;
    previous_close: string | null;
    gap_percentage: string | null;
  };
  support_resistance: {
    nearest_support: string | null;
    nearest_resistance: string | null;
    distance_to_support_percentage: string | null;
    distance_to_resistance_percentage: string | null;
    breakout_risk: boolean | null;
  };
  provider: string;
  timestamp: string;
};
