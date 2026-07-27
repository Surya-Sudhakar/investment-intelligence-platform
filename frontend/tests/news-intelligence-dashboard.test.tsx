import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { NewsIntelligenceDashboard } from "@/components/news/news-intelligence-dashboard";

afterEach(() => vi.restoreAllMocks());

it("renders summary, sentiment, grouped stories, and articles", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(
      JSON.stringify({
        symbol: "AAPL",
        asset_type: "STOCK",
        provider: "test",
        articles: [
          {
            id: "1",
            title: "Apple raises guidance",
            summary: "Revenue improved.",
            source: "Example",
            published_at: "2026-07-27T10:00:00Z",
            url: "https://example.com/1",
            category: "EARNINGS",
            relevance_score: 90,
            sentiment: "POSITIVE",
            confidence: 85,
            freshness: { state: "FRESH", age_seconds: 10 },
          },
        ],
        groups: [
          {
            id: "g",
            title: "Apple raises guidance",
            summary: "Revenue improved.",
            article_count: 1,
            sources: ["Example"],
            sentiment: "POSITIVE",
            confidence: 85,
          },
        ],
        aggregate: {
          positive_count: 1,
          neutral_count: 0,
          negative_count: 0,
          unknown_count: 0,
          overall_sentiment: "POSITIVE",
          confidence: 85,
          explanation: "One article.",
        },
        summary: "Apple raised guidance.",
        freshness: { state: "FRESH", age_seconds: 10 },
        generated_at: "2026-07-27T10:00:00Z",
        warnings: [],
      }),
      { status: 200, headers: { "Content-Type": "application/json" } },
    ),
  );
  render(
    <QueryClientProvider client={new QueryClient()}>
      <NewsIntelligenceDashboard />
    </QueryClientProvider>,
  );
  await userEvent.click(screen.getByRole("button", { name: "Load news" }));
  expect(await screen.findByText("Apple raised guidance.")).toBeInTheDocument();
  expect(screen.getAllByText("POSITIVE").length).toBeGreaterThan(0);
  expect(screen.getByText("Grouped Stories")).toBeInTheDocument();
});
