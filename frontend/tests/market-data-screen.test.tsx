import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MarketDataScreen } from "@/components/market-data/market-data-screen";

const provider = {
  provider_name: "alpha_vantage",
  historical_candles: true,
  latest_quote: true,
  symbol_search: true,
  symbol_details: true,
  websocket_prices: false,
  bid_ask: false,
  market_status: false,
  delayed_flag: true,
  supported_intervals: ["5min", "15min", "1h", "1day"],
  supported_asset_classes: ["stock"],
  maximum_candle_limit: 500,
  free_plan_limitations: [],
  rate_limit_description: "25 requests per day",
};
const health = {
  provider: "alpha_vantage",
  configured: true,
  reachable: true,
  authenticated: true,
  latency_ms: 10,
  last_checked_at: "2026-07-24T00:00:00Z",
  message: "Provider responded successfully.",
};

function json(body: object, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

function renderScreen() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MarketDataScreen />
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("MarketDataScreen", () => {
  it("displays provider capabilities and health", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      return url.endsWith("/market-data/provider")
        ? json(provider)
        : json(health);
    });
    renderScreen();
    expect(await screen.findByText("alpha_vantage")).toBeInTheDocument();
    expect(await screen.findByText(/Reachable/)).toBeInTheDocument();
  });

  it("searches, selects a symbol, and retrieves candles and a quote", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.endsWith("/market-data/provider")) return json(provider);
      if (url.endsWith("/market-data/health")) return json(health);
      if (url.includes("/symbols/search"))
        return json([
          {
            symbol: "AAPL",
            name: "Apple Inc.",
            exchange: "NASDAQ",
            currency: "USD",
            country: "USA",
            asset_type: "stock",
            provider: "alpha_vantage",
            provider_symbol: "AAPL",
          },
        ]);
      if (url.includes("/candles"))
        return json({
          data: {
            symbol: "AAPL",
            interval: "1day",
            candles: [
              {
                symbol: "AAPL",
                interval: "1day",
                time: "2026-07-23T00:00:00Z",
                open: "10",
                high: "12",
                low: "9",
                close: "11",
                volume: 100,
                data_status: "END_OF_DAY",
              },
            ],
            provider: "alpha_vantage",
            count: 1,
            received_count: 1,
            rejected_count: 0,
            requested_at: "2026-07-24T00:00:00Z",
            source_timezone: "UTC",
            data_status: "END_OF_DAY",
            cached: false,
          },
        });
      return json({
        symbol: "AAPL",
        price: "11",
        bid: null,
        ask: null,
        spread: null,
        open: "10",
        high: "12",
        low: "9",
        previous_close: "10",
        change: "1",
        change_percentage: "10",
        volume: 100,
        timestamp: "2026-07-23T00:00:00Z",
        received_at: "2026-07-24T00:00:00Z",
        provider: "alpha_vantage",
        delayed: true,
        market_open: null,
        data_status: "END_OF_DAY",
        age_seconds: 86400,
        cached: false,
      });
    });
    renderScreen();
    await userEvent.type(screen.getByLabelText("Search stocks"), "Apple");
    expect(await screen.findByText(/Apple Inc/)).toBeInTheDocument();
    await userEvent.click(screen.getByText(/Apple Inc/));
    await userEvent.click(screen.getByRole("button", { name: "Load candles" }));
    expect(await screen.findByText("2026-07-23T00:00:00Z")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Latest quote" }));
    expect(await screen.findByText(/Price 11/)).toBeInTheDocument();
  });

  it("shows provider and empty-candle errors", async () => {
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      const url = String(input);
      if (url.endsWith("/market-data/provider")) return json(provider);
      if (url.endsWith("/market-data/health"))
        return Promise.reject(new TypeError("offline"));
      if (url.includes("/candles"))
        return json({
          data: {
            symbol: "AAPL",
            interval: "1day",
            candles: [],
            provider: "alpha_vantage",
            count: 0,
            received_count: 0,
            rejected_count: 0,
            requested_at: "2026-07-24T00:00:00Z",
            source_timezone: "UTC",
            data_status: "UNKNOWN",
            cached: false,
          },
        });
      return json([]);
    });
    renderScreen();
    expect(
      await screen.findByText(/Cannot connect to the backend/),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Selected symbol"), {
      target: { value: "AAPL" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Load candles" }));
    await waitFor(() =>
      expect(
        screen.getByText("No candles returned for this request."),
      ).toBeInTheDocument(),
    );
  });
});
