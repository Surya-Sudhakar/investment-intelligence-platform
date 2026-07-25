"use client";

import { useQuery } from "@tanstack/react-query";

import { marketDataApi } from "@/lib/api/market-data";
import type { Interval } from "@/lib/api/market-data-types";
import { ApiError } from "@/lib/api/client";

export const marketDataKeys = {
  provider: ["market-data", "provider"] as const,
  health: ["market-data", "health"] as const,
  search: (query: string) => ["market-data", "search", query] as const,
  symbol: (symbol: string) => ["market-data", "symbol", symbol] as const,
  candles: (symbol: string, interval: Interval, limit: number) =>
    ["market-data", "candles", symbol, interval, limit] as const,
  quote: (symbol: string) => ["market-data", "quote", symbol] as const,
};

export function useProviderInformation() {
  const retryConnection = (failureCount: number, error: Error) =>
    error instanceof ApiError &&
    error.code === "CONNECTION_ERROR" &&
    failureCount < 3;
  const provider = useQuery({
    queryKey: marketDataKeys.provider,
    queryFn: ({ signal }) => marketDataApi.provider(signal),
    retry: retryConnection,
    retryDelay: 1_000,
  });
  const health = useQuery({
    queryKey: marketDataKeys.health,
    queryFn: ({ signal }) => marketDataApi.health(signal),
    retry: retryConnection,
    retryDelay: 1_000,
  });
  return { provider, health };
}

export function useSymbolSearch(query: string) {
  return useQuery({
    queryKey: marketDataKeys.search(query),
    queryFn: ({ signal }) => marketDataApi.search(query, signal),
    enabled: query.trim().length >= 2,
  });
}

export function useCandles(symbol: string, interval: Interval, limit: number) {
  return useQuery({
    queryKey: marketDataKeys.candles(symbol, interval, limit),
    queryFn: ({ signal }) =>
      marketDataApi.candles(symbol, interval, limit, signal),
    enabled: false,
    retry: false,
  });
}

export function useQuote(symbol: string) {
  return useQuery({
    queryKey: marketDataKeys.quote(symbol),
    queryFn: ({ signal }) => marketDataApi.quote(symbol, signal),
    enabled: false,
    retry: false,
  });
}
