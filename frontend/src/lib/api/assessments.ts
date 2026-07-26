import { apiGet } from "./client";
import type { TechnicalAssessment } from "./assessment-types";

export const assessmentsApi = {
  get: (symbol: string, signal?: AbortSignal) =>
    apiGet<TechnicalAssessment>(
      `/assessments/${encodeURIComponent(symbol)}?interval=1day`,
      signal,
    ),
};
