import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AssetIntelligenceDashboard } from "@/components/assets/asset-intelligence-dashboard";

const base = {
  symbol: "AAPL",
  display_name: "Apple Inc.",
  asset_type: "STOCK",
  exchange: "NASDAQ",
  currency: "USD",
  provider: "test",
  source_timestamp: "2026-07-26T12:00:00Z",
  generated_at: "2026-07-26T12:01:00Z",
  freshness: { state: "LIVE", age_seconds: 60, reason: "Current." },
  profile: { company_name: "Apple Inc.", sector: "Technology" },
  metrics: { pe_ratio: "25", revenue: null },
  classification: { overall: "POSITIVE" },
  warnings: [],
  availability: {
    profile: true,
    metrics: true,
    fundamentals: true,
    holdings: false,
    allocations: false,
    technical_snapshot: false,
  },
};

afterEach(() => vi.restoreAllMocks());

function renderDashboard(payload: object) {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify(payload), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <AssetIntelligenceDashboard />
    </QueryClientProvider>,
  );
}

describe("AssetIntelligenceDashboard", () => {
  it("renders stock fundamentals and unavailable values", async () => {
    renderDashboard(base);
    await userEvent.click(screen.getByRole("button", { name: "Inspect" }));
    expect(await screen.findByText("Company profile")).toBeInTheDocument();
    expect(screen.getByText("Technology")).toBeInTheDocument();
    expect(screen.getByText("POSITIVE")).toBeInTheDocument();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
  });

  it("renders gold note and stale warning", async () => {
    renderDashboard({
      ...base,
      symbol: "XAUUSD",
      display_name: "Gold Spot / US Dollar",
      asset_type: "GOLD",
      freshness: { state: "STALE", age_seconds: 1000, reason: "Old." },
      profile: {
        note: "Company fundamentals are not applicable to gold.",
      },
      metrics: { current_price: "2400" },
      classification: null,
      warnings: ["The latest market observation is stale."],
    });
    await userEvent.click(screen.getByRole("button", { name: "Inspect" }));
    expect(await screen.findByText("Gold instrument")).toBeInTheDocument();
    expect(
      screen.getByText("Company fundamentals are not applicable to gold."),
    ).toBeInTheDocument();
    expect(
      screen.getByText("This market observation is stale."),
    ).toBeInTheDocument();
  });

  it("renders ETF partial-data warning", async () => {
    renderDashboard({
      ...base,
      symbol: "GLD",
      display_name: "SPDR Gold Shares",
      asset_type: "ETF",
      profile: { fund_name: "SPDR Gold Shares" },
      metrics: { expense_ratio_percentage: "0.4" },
      classification: null,
      warnings: ["Holdings are unavailable."],
    });
    await userEvent.click(screen.getByRole("button", { name: "Inspect" }));
    expect(await screen.findByText("Fund profile")).toBeInTheDocument();
    expect(screen.getByText("Partial or limited data")).toBeInTheDocument();
    expect(screen.getByText("Holdings are unavailable.")).toBeInTheDocument();
  });

  it("renders provider errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          error: { code: "UNSUPPORTED_ASSET", message: "Unsupported asset." },
        }),
        { status: 422, headers: { "Content-Type": "application/json" } },
      ),
    );
    render(
      <QueryClientProvider client={new QueryClient()}>
        <AssetIntelligenceDashboard />
      </QueryClientProvider>,
    );
    await userEvent.click(screen.getByRole("button", { name: "Inspect" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unsupported asset.",
    );
  });
});
