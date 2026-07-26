"use client";

import { useQuery } from "@tanstack/react-query";

import { intelligenceApi } from "@/lib/api/intelligence";

export function useIntelligence(symbol: string) {
  return useQuery({
    queryKey: ["intelligence", symbol],
    queryFn: ({ signal }) => intelligenceApi.snapshot(symbol, signal),
    enabled: Boolean(symbol),
    // Respect the free provider's 25-request daily allowance.
    refetchInterval: (query) =>
      query.state.error ? false : 4 * 60 * 60 * 1_000,
    retry: false,
  });
}
