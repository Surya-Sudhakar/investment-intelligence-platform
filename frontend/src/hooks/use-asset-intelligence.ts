"use client";

import { useQuery } from "@tanstack/react-query";

import { assetsApi } from "@/lib/api/assets";

export function useAssetIntelligence(symbol: string) {
  return useQuery({
    queryKey: ["asset-intelligence", symbol],
    queryFn: ({ signal }) => assetsApi.intelligence(symbol, signal),
    enabled: Boolean(symbol),
    staleTime: 5 * 60 * 1_000,
    retry: false,
  });
}
