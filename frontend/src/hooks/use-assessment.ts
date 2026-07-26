"use client";

import { useQuery } from "@tanstack/react-query";

import { assessmentsApi } from "@/lib/api/assessments";

export function useAssessment(symbol: string) {
  return useQuery({
    queryKey: ["technical-assessment", symbol, "1day"],
    queryFn: ({ signal }) => assessmentsApi.get(symbol, signal),
    enabled: Boolean(symbol),
    refetchInterval: (query) =>
      query.state.error ? false : 4 * 60 * 60 * 1_000,
    retry: false,
  });
}
