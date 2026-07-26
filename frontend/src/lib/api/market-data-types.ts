export type Interval = "5min" | "15min" | "1h" | "1day";
export type DataStatus = "UNKNOWN" | "DELAYED" | "CACHED" | "END_OF_DAY";

export interface ProviderCapabilities {
  provider_name: string;
  historical_candles: boolean;
  latest_quote: boolean;
  symbol_search: boolean;
  symbol_details: boolean;
  websocket_prices: boolean;
  bid_ask: boolean;
  market_status: boolean;
  delayed_flag: boolean;
  supported_intervals: Interval[];
  supported_asset_classes: ["stock"];
  maximum_candle_limit: number;
  free_plan_limitations: string[];
  rate_limit_description: string;
}

export interface ProviderHealth {
  provider: string;
  configured: boolean;
  reachable: boolean;
  authenticated: boolean;
  latency_ms: number | null;
  last_checked_at: string;
  message: string;
}

export interface SymbolResult {
  symbol: string;
  name: string;
  exchange: string | null;
  currency: string | null;
  country: string | null;
  asset_type: "stock";
  provider: string;
  provider_symbol: string;
}

export interface Candle {
  symbol: string;
  interval: Interval;
  time: string;
  open: string;
  high: string;
  low: string;
  close: string;
  volume: number | null;
  data_status: DataStatus;
}

export interface CandleResponse {
  data: {
    symbol: string;
    interval: Interval;
    candles: Candle[];
    provider: string;
    count: number;
    received_count: number;
    rejected_count: number;
    requested_at: string;
    source_timezone: string | null;
    data_status: DataStatus;
    cached: boolean;
  };
}

export interface Quote {
  symbol: string;
  price: string;
  bid: string | null;
  ask: string | null;
  spread: string | null;
  open: string | null;
  high: string | null;
  low: string | null;
  previous_close: string | null;
  change: string | null;
  change_percentage: string | null;
  volume: number | null;
  timestamp: string;
  received_at: string;
  provider: string;
  delayed: boolean;
  market_open: boolean | null;
  data_status: DataStatus;
  age_seconds: number;
  cached: boolean;
}
