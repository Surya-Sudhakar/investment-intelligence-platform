"use client";

import { useQuery } from "@tanstack/react-query";

import { apiGet } from "@/lib/api/client";
import type { HealthResponse, ReadyResponse } from "@/lib/api/types";

export function useSystemStatus() {
  const health = useQuery({
    queryKey: ["health"],
    queryFn: ({ signal }) => apiGet<HealthResponse>("/health", signal),
  });
  const readiness = useQuery({
    queryKey: ["readiness"],
    queryFn: ({ signal }) => apiGet<ReadyResponse>("/ready", signal),
  });
  return { health, readiness };
}
