import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { IntelligenceDashboard } from "@/components/intelligence/intelligence-dashboard";

const snapshot = {
  symbol: "AAPL",
  quote: { price: "210" },
  freshness: { state: "DELAYED", age_seconds: 10, reason: "Provider delayed." },
  market_status: { state: "OPEN", exchange_timezone: "UTC", reason: "Open." },
  trend: "UPTREND",
  momentum: "BULLISH",
  volatility: "NORMAL",
  indicators: {
    ema20: "205",
    ema50: "200",
    rsi14: "61",
    atr14: "3",
    average_volume: "1000",
    high_52_week: "220",
    low_52_week: "150",
    daily_change_percentage: "1",
    previous_close: "208",
    gap_percentage: "0.5",
  },
  support_resistance: {
    nearest_support: "200",
    nearest_resistance: "215",
    distance_to_support_percentage: "4.76",
    distance_to_resistance_percentage: "2.38",
    breakout_risk: false,
  },
  provider: "test",
  timestamp: "2026-07-24T12:00:00Z",
};

afterEach(() => vi.restoreAllMocks());

describe("IntelligenceDashboard", () => {
  it("loads and displays a normalized snapshot", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(snapshot), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const client = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    render(
      <QueryClientProvider client={client}>
        <IntelligenceDashboard />
      </QueryClientProvider>,
    );
    await userEvent.click(screen.getByRole("button", { name: "Analyze" }));
    expect(await screen.findByText("UPTREND")).toBeInTheDocument();
    expect(screen.getByText("61")).toBeInTheDocument();
    expect(screen.getByText("Provider delayed.")).toBeInTheDocument();
    expect(
      screen.getByText(/does not provide recommendations/i),
    ).toBeInTheDocument();
  });
});
