import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DevelopmentStatus } from "@/components/status/development-status";

const health = {
  status: "healthy",
  service: "API",
  version: "0.1.0",
  timestamp: "2026-07-24T00:00:00Z",
};
const ready = {
  status: "ready",
  service: "API",
  version: "0.1.0",
  timestamp: "2026-07-24T00:00:00Z",
  application: "initialized",
  database: "connected",
};

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <DevelopmentStatus />
    </QueryClientProvider>,
  );
}

afterEach(() => vi.restoreAllMocks());

describe("DevelopmentStatus", () => {
  it("renders the project and loading state", () => {
    vi.spyOn(globalThis, "fetch").mockImplementation(
      () => new Promise(() => {}),
    );
    renderPage();
    expect(
      screen.getByText("AI Investment Intelligence Platform"),
    ).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Checking backend connectivity",
    );
  });

  it("renders successful health and readiness responses", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(JSON.stringify(health), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(ready), { status: 200 }),
      );
    renderPage();
    expect(await screen.findByText("Connected")).toBeInTheDocument();
    expect(screen.getByText("0.1.0")).toBeInTheDocument();
    expect(screen.getByText("connected")).toBeInTheDocument();
  });

  it("renders a backend-unavailable state", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("offline"));
    renderPage();
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Backend unavailable",
    );
  });
});
