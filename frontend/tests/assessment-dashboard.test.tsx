import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AssessmentDashboard } from "@/components/assessments/assessment-dashboard";

const assessment = {
  symbol: "AAPL",
  interval: "1day",
  time_horizon: "SWING_POSITION",
  assessment: "BULLISH",
  technical_score: 72,
  confidence_score: 88,
  risk: {
    score: 43,
    level: "ELEVATED",
    data_coverage_percentage: 100,
    components: [],
  },
  components: [
    {
      name: "trend",
      weight: 20,
      available: true,
      raw_value: "UPTREND",
      signal: 0.7,
      weighted_contribution: 14,
      explanation: "Trend is upward.",
    },
  ],
  supporting_factors: [{ code: "TREND", message: "Trend is upward." }],
  conflicting_factors: [],
  risk_factors: [{ code: "ATR", message: "Volatility is elevated." }],
  missing_data_factors: [],
  data_quality: {
    freshness_state: "DELAYED",
    source_age_seconds: 60,
    quote_data_status: "DELAYED",
    quote_cached: false,
    market_status: "OPEN",
    available_directional_weight: 100,
    eligible_directional_weight: 100,
    input_coverage_percentage: 100,
    issues: [],
  },
  scoring_version: "technical-v1",
  snapshot_timestamp: "2026-07-25T12:00:00Z",
  generated_at: "2026-07-25T12:00:01Z",
};

afterEach(() => vi.restoreAllMocks());

describe("AssessmentDashboard", () => {
  it("renders scores, explanations, and methodology", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(assessment), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={client}>
        <AssessmentDashboard />
      </QueryClientProvider>,
    );
    await userEvent.click(screen.getByRole("button", { name: "Assess" }));
    expect(await screen.findByText("BULLISH")).toBeInTheDocument();
    expect(screen.getByText("72/100")).toBeInTheDocument();
    expect(screen.getByText("88/100")).toBeInTheDocument();
    expect(screen.getByText(/technical-v1/)).toBeInTheDocument();
    expect(screen.getAllByText("Trend is upward.")).toHaveLength(2);
  });
});
