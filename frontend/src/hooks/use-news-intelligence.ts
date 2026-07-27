"use client";

import { useQuery } from "@tanstack/react-query";
import { newsApi } from "@/lib/api/news";

export function useNewsIntelligence(symbol: string) {
  return useQuery({
    queryKey: ["news-intelligence", symbol],
    queryFn: ({ signal }) => newsApi.get(symbol, signal),
    enabled: Boolean(symbol),
    staleTime: 15 * 60 * 1000,
    retry: false,
  });
}
