import { apiGet } from "./client";
import type { NewsIntelligence } from "./news-types";

export const newsApi = {
  get: (symbol: string, signal?: AbortSignal) =>
    apiGet<NewsIntelligence>(
      `/assets/${encodeURIComponent(symbol)}/news?limit=20`,
      signal,
    ),
};
