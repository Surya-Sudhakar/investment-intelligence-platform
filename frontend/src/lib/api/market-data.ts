import { apiGet } from "./client";
import type {
  CandleResponse,
  Interval,
  ProviderCapabilities,
  ProviderHealth,
  Quote,
  SymbolResult,
} from "./market-data-types";

export const marketDataApi = {
  provider: (signal?: AbortSignal) =>
    apiGet<ProviderCapabilities>("/market-data/provider", signal),
  health: (signal?: AbortSignal) =>
    apiGet<ProviderHealth>("/market-data/health", signal),
  search: (query: string, signal?: AbortSignal) =>
    apiGet<SymbolResult[]>(
      `/symbols/search?q=${encodeURIComponent(query)}&limit=10`,
      signal,
    ),
  symbol: (symbol: string, signal?: AbortSignal) =>
    apiGet<SymbolResult>(`/symbols/${encodeURIComponent(symbol)}`, signal),
  candles: (
    symbol: string,
    interval: Interval,
    limit: number,
    signal?: AbortSignal,
  ) =>
    apiGet<CandleResponse>(
      `/market-data/${encodeURIComponent(symbol)}/candles?interval=${interval}&limit=${limit}`,
      signal,
    ),
  quote: (symbol: string, signal?: AbortSignal) =>
    apiGet<Quote>(`/market-data/${encodeURIComponent(symbol)}/quote`, signal),
};
