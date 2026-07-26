import { apiGet } from "./client";
import type { IntelligenceSnapshot } from "./intelligence-types";

export const intelligenceApi = {
  snapshot: (symbol: string, signal?: AbortSignal) =>
    apiGet<IntelligenceSnapshot>(
      `/intelligence/${encodeURIComponent(symbol)}`,
      signal,
    ),
};
