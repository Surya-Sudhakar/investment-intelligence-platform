import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";

import { MarketContextDashboard } from "@/components/market-context/market-context-dashboard";
import type { MarketContext } from "@/lib/api/market-context-types";

afterEach(() => vi.restoreAllMocks());

const unavailable = (reason: string) => ({
  status: "unavailable",
  value: null,
  reason,
});

const notApplicable = (reason: string) => ({
  status: "not_applicable",
  value: null,
  reason,
});

function response(): MarketContext {
  const reason = "Not supplied.";
  return {
    symbol: "AAPL",
    display_name: "Apple Inc.",
    asset_type: "STOCK",
    provider: "test",
    methodology_version: "market-context-v1",
    horizon: { interval: "1day", lookback_sessions: 20 },
    overall_context: {
      status: "available",
      value: "POSITIVE",
      reason: "Calculated.",
    },
    confidence: 82,
    partial_data_status: "partial",
    market: {
      primary_exchange: {
        status: "available",
        value: "NASDAQ",
        reason: "Available.",
      },
      primary_market_index: unavailable(reason),
      reference: unavailable(reason),
      performance: unavailable(reason),
    },
    sector: {
      name: { status: "available", value: "Technology", reason: "Available." },
      reference: unavailable(reason),
      performance: unavailable(reason),
      trend: unavailable(reason),
    },
    industry: {
      name: { status: "available", value: "Software", reason: "Available." },
      reference: unavailable(reason),
      performance: unavailable(reason),
      trend: unavailable(reason),
    },
    commodity: {
      precious_metals_trend: notApplicable(reason),
      silver_comparison: notApplicable(reason),
      commodity_index_trend: notApplicable(reason),
      safe_haven_demand_trend: notApplicable(reason),
      commodity_market_alignment: notApplicable(reason),
    },
    etf: {
      etf_category: notApplicable(reason),
      fund_category: notApplicable(reason),
      benchmark_index: notApplicable(reason),
      regional_exposure: notApplicable(reason),
      sector_concentration: notApplicable(reason),
      relative_performance: notApplicable(reason),
    },
    relative_strength: {
      versus_market: unavailable(reason),
      versus_sector: unavailable(reason),
      versus_industry: unavailable(reason),
    },
    supporting_observations: ["AAPL outperformed its market reference."],
    warnings: ["Industry comparison is unavailable."],
    freshness: {
      status: "available",
      state: "CURRENT",
      oldest_source_timestamp: "2026-07-26T00:00:00Z",
      newest_source_timestamp: "2026-07-26T00:00:00Z",
      age_days: 1,
      reason: "Current.",
    },
    availability: {
      asset_performance: "available",
      market: "unavailable",
      sector: "unavailable",
      industry: "unavailable",
      relative_strength: "unavailable",
      commodity: "not_applicable",
      etf: "not_applicable",
    },
    source_timestamp: {
      status: "available",
      value: "2026-07-26T00:00:00Z",
      reason: "Available.",
    },
    generated_at: "2026-07-27T10:00:00Z",
  } as MarketContext;
}

function renderDashboard() {
  render(
    <QueryClientProvider
      client={
        new QueryClient({
          defaultOptions: { queries: { retry: false } },
        })
      }
    >
      <MarketContextDashboard />
    </QueryClientProvider>,
  );
}

it("renders stock context, confidence, observations, and partial data", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(response()), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
  renderDashboard();

  await userEvent.click(screen.getByRole("button", { name: "Load context" }));

  expect(await screen.findByText("POSITIVE")).toBeInTheDocument();
  expect(screen.getByText("82%")).toBeInTheDocument();
  expect(screen.getByText("Technology")).toBeInTheDocument();
  expect(
    screen.getByText("AAPL outperformed its market reference."),
  ).toBeInTheDocument();
  expect(screen.getByText("Partial or limited data")).toBeInTheDocument();
});

it("renders loading and standardized error states", async () => {
  let resolveFetch: ((value: Response) => void) | undefined;
  vi.spyOn(globalThis, "fetch").mockImplementation(
    () =>
      new Promise<Response>((resolve) => {
        resolveFetch = resolve;
      }),
  );
  renderDashboard();
  await userEvent.click(screen.getByRole("button", { name: "Load context" }));
  expect(screen.getByRole("status")).toHaveTextContent(
    "Loading market context",
  );

  resolveFetch?.(
    new Response(
      JSON.stringify({
        error: { code: "MARKET_PROVIDER_UNAVAILABLE", message: "Unavailable." },
      }),
      { status: 503, headers: { "Content-Type": "application/json" } },
    ),
  );
  expect(await screen.findByRole("alert")).toHaveTextContent("Unavailable.");
  expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
});

it("renders gold commodity context and the Phase 8 boundary", async () => {
  const payload = response();
  payload.asset_type = "GOLD";
  payload.commodity.safe_haven_demand_trend = {
    status: "planned_phase8",
    value: null,
    reason: "Requires Phase 8 inputs.",
  };
  payload.commodity.precious_metals_trend = {
    status: "available",
    value: "STRONG",
    reason: "Calculated.",
  };
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(payload), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
  renderDashboard();
  await userEvent.click(screen.getByRole("button", { name: "Load context" }));

  expect(await screen.findByText("Commodity context")).toBeInTheDocument();
  expect(screen.getByText(/Planned for Phase 8/)).toBeInTheDocument();
});

it("renders ETF category and structured missing benchmark", async () => {
  const payload = response();
  payload.asset_type = "ETF";
  payload.etf.fund_category = {
    status: "available",
    value: "Large blend",
    reason: "Provided.",
  };
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(payload), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
  renderDashboard();
  await userEvent.click(screen.getByRole("button", { name: "Load context" }));

  expect(await screen.findByText("ETF context")).toBeInTheDocument();
  expect(screen.getByText("Large blend")).toBeInTheDocument();
  expect(screen.getAllByText(/Unavailable/).length).toBeGreaterThan(0);
});

it("discloses actual aligned observations", async () => {
  const payload = response();
  payload.relative_strength.versus_market = {
    status: "available",
    value: {
      asset_symbol: "AAPL",
      reference: {
        symbol: "SPY",
        name: "SPDR S&P 500 ETF Trust",
        kind: "MARKET_PROXY",
        is_proxy: true,
      },
      difference_percentage_points: "2.40",
      classification: "STRONG",
      overlapping_observations: 18,
    },
    reason: "Calculated from shared dates.",
    alignment: {
      actual_overlap_count: 18,
      aligned_start_timestamp: "2026-06-30T00:00:00Z",
      aligned_end_timestamp: "2026-07-25T00:00:00Z",
      requested_lookback: 20,
      minimum_required: 15,
      alignment_sufficient: true,
    },
  };
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(payload), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
  renderDashboard();
  await userEvent.click(screen.getByRole("button", { name: "Load context" }));

  expect(
    await screen.findByText(/18 aligned daily observations/),
  ).toBeInTheDocument();
});
