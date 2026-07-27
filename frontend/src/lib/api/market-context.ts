import { apiGet } from "./client";
import type { MarketContext } from "./market-context-types";

export const marketContextApi = {
  get: (symbol: string, signal?: AbortSignal) =>
    apiGet<MarketContext>(
      `/assets/${encodeURIComponent(symbol)}/market-context`,
      signal,
    ),
};
