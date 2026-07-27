"use client";

import { useQuery } from "@tanstack/react-query";

import { marketContextApi } from "@/lib/api/market-context";

export function useMarketContext(symbol: string) {
  return useQuery({
    queryKey: ["market-context", symbol],
    queryFn: ({ signal }) => marketContextApi.get(symbol, signal),
    enabled: Boolean(symbol),
    staleTime: 5 * 60 * 1_000,
    retry: false,
  });
}
