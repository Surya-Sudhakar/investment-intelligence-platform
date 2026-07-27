import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LocalWatchlist } from "@/components/watchlist/local-watchlist";
import { AssetWorkspace } from "@/components/workspaces/asset-workspace";
import { ResearchDashboard } from "@/components/workspaces/research-dashboard";

vi.mock("@tanstack/react-query", () => ({
  useQuery: () => ({
    data: {
      data: {
        candles: [{ close: "100" }, { close: "102" }, { close: "101" }],
      },
    },
    isLoading: false,
  }),
}));

vi.mock("@/hooks/use-intelligence", () => ({
  useIntelligence: () => ({
    data: {
      quote: {
        price: "231.42",
        change_percentage: "0.93",
        data_status: "DELAYED",
        provider: "test",
      },
      trend: "UPTREND",
      momentum: "BULLISH",
      volatility: "NORMAL",
      indicators: { rsi14: "58", ema20: "225", ema50: "210" },
      support_resistance: {
        nearest_support: "220",
        nearest_resistance: "235",
      },
      timestamp: "2026-07-27T00:00:00Z",
    },
    isLoading: false,
    isError: false,
  }),
}));

vi.mock("@/hooks/use-assessment", () => ({
  useAssessment: () => ({
    data: {
      assessment: "BULLISH",
      technical_score: 72,
      confidence_score: 81,
      risk: { level: "MODERATE", score: 42 },
      scoring_version: "technical-v1",
      supporting_factors: [{ code: "trend", message: "Trend is supportive." }],
    },
    isLoading: false,
    isError: false,
  }),
}));

vi.mock("@/hooks/use-asset-intelligence", () => ({
  useAssetIntelligence: () => ({
    data: {
      display_name: "Apple Inc.",
      asset_type: "STOCK",
      exchange: "NASDAQ",
      currency: "USD",
      provider: "test",
      warnings: [],
      profile: { sector: "Technology" },
      metrics: {},
    },
    isLoading: false,
    isError: false,
  }),
}));

vi.mock("@/hooks/use-news-intelligence", () => ({
  useNewsIntelligence: () => ({
    data: {
      aggregate: { overall_sentiment: "POSITIVE", confidence: 68 },
      warnings: [],
      summary: "Coverage is constructive.",
      articles: [],
    },
    isLoading: false,
    isError: false,
  }),
}));

vi.mock("@/hooks/use-market-context", () => ({
  useMarketContext: () => ({
    data: {
      methodology_version: "market-context-v1",
      warnings: [],
      overall_context: { value: "STRONG", reason: "Aligned comparison." },
      confidence: 78,
      partial_data_status: "complete",
      freshness: { state: "CURRENT" },
      supporting_observations: ["Asset outperformed its market reference."],
    },
    isLoading: false,
    isError: false,
  }),
}));

describe("prototype-backed UI workspaces", () => {
  beforeEach(() => localStorage.clear());

  it("renders the research dashboard without fabricated prices", () => {
    render(<ResearchDashboard />);
    expect(
      screen.getByRole("heading", { name: "Market intelligence" }),
    ).toBeInTheDocument();
    expect(screen.getByText("AAPL")).toBeInTheDocument();
    expect(screen.getByText(/No BUY, SELL, HOLD/)).toBeInTheDocument();
  });

  it("renders normalized Phase 2–7 workspace evidence", () => {
    render(<AssetWorkspace symbol="AAPL" />);
    expect(screen.getByText("Apple Inc.")).toBeInTheDocument();
    expect(screen.getByText("BULLISH")).toBeInTheDocument();
    expect(screen.getByText("Coverage is constructive.")).toBeInTheDocument();
    expect(screen.getByText("STRONG")).toBeInTheDocument();
  });

  it("loads and removes browser-local watchlist items", async () => {
    localStorage.setItem(
      "meridian-watchlist",
      JSON.stringify([
        { symbol: "SPY", name: "SPDR S&P 500 ETF", type: "ETF" },
      ]),
    );
    render(<LocalWatchlist />);
    await waitFor(() => expect(screen.getByText("SPY")).toBeInTheDocument());
    await userEvent.click(screen.getByRole("button", { name: "Remove" }));
    expect(screen.getByText("Your watchlist is empty")).toBeInTheDocument();
  });

  it("adds an asset to the browser-local watchlist", async () => {
    const { unmount } = render(<AssetWorkspace symbol="AAPL" />);
    await userEvent.click(
      screen.getByRole("button", { name: "☆ Add to watchlist" }),
    );
    expect(screen.getByText("Added to watchlist")).toBeInTheDocument();
    unmount();

    render(<LocalWatchlist />);
    await waitFor(() => expect(screen.getByText("AAPL")).toBeInTheDocument());
    expect(screen.getByText("Apple Inc.")).toBeInTheDocument();
  });
});
