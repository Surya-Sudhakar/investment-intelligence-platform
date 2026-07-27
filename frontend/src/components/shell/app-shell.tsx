"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { marketDataApi } from "@/lib/api/market-data";
import type { SymbolResult } from "@/lib/api/market-data-types";

export function AppShell({
  children,
  active,
}: {
  children: React.ReactNode;
  active: "dashboard" | "watchlist" | "workspace";
}) {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SymbolResult[]>([]);

  useEffect(() => {
    if (query.trim().length < 2) {
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      marketDataApi
        .search(query.trim(), controller.signal)
        .then(setResults)
        .catch(() => setResults([]));
    }, 300);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  const open = (symbol: string) => {
    setQuery("");
    setResults([]);
    router.push(`/assets/${encodeURIComponent(symbol)}`);
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link className="brand" href="/">
          <span className="brand-mark">M</span>
          <span>
            <span className="brand-name">Meridian</span>
            <span className="brand-sub">Intelligence</span>
          </span>
        </Link>
        <nav className="nav" aria-label="Primary navigation">
          <Link
            className={`nav-link ${active === "dashboard" ? "active" : ""}`}
            href="/"
          >
            <span className="nav-icon">◆</span>Dashboard
          </Link>
          <Link
            className={`nav-link ${active === "watchlist" ? "active" : ""}`}
            href="/watchlist"
          >
            <span className="nav-icon">☆</span>Watchlist
          </Link>
          <span className="nav-link" aria-disabled="true">
            <span className="nav-icon">◌</span>Macro context{" "}
            <span className="badge">Phase 8</span>
          </span>
        </nav>
        <div className="sidebar-footer">
          <div className="provider-pill">
            <span className="status-dot" />
            Phase 1–7 platform
          </div>
        </div>
      </aside>
      <div className="app-main">
        <header className="topbar">
          <div className="global-search">
            <input
              aria-label="Search assets"
              className="search-input"
              placeholder="Search symbols or companies…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && query.trim())
                  open(query.trim().toUpperCase());
              }}
            />
            {query.trim().length >= 2 && results.length > 0 && (
              <div className="search-results">
                {results.map((result) => (
                  <button
                    className="search-result"
                    key={`${result.provider}:${result.provider_symbol}`}
                    onClick={() => open(result.symbol)}
                    type="button"
                  >
                    <span>
                      <span className="search-symbol">{result.symbol}</span>
                      <br />
                      <span className="search-name">{result.name}</span>
                    </span>
                    <span className="badge">
                      {result.exchange ?? "Unknown"}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>
          <span className="muted" style={{ marginLeft: "auto", fontSize: 11 }}>
            Deterministic research · no recommendations
          </span>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}
