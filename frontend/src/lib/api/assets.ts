import { apiGet } from "./client";
import type { AssetIntelligence } from "./asset-intelligence-types";

export const assetsApi = {
  intelligence: (symbol: string, signal?: AbortSignal) =>
    apiGet<AssetIntelligence>(
      `/assets/${encodeURIComponent(symbol)}/intelligence`,
      signal,
    ),
};
