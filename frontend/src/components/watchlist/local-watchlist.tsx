"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import {
  readWatchlist,
  WATCHLIST_CHANGED_EVENT,
  writeWatchlist,
  type WatchItem,
} from "@/lib/watchlist";

export function LocalWatchlist() {
  const [items, setItems] = useState<WatchItem[]>([]);
  const [query, setQuery] = useState("");
  useEffect(() => {
    const update = () => setItems(readWatchlist());
    update();
    window.addEventListener("storage", update);
    window.addEventListener(WATCHLIST_CHANGED_EVENT, update);
    return () => {
      window.removeEventListener("storage", update);
      window.removeEventListener(WATCHLIST_CHANGED_EVENT, update);
    };
  }, []);
  const visible = useMemo(
    () =>
      items.filter((item) =>
        `${item.symbol} ${item.name}`
          .toLowerCase()
          .includes(query.toLowerCase()),
      ),
    [items, query],
  );
  const remove = (symbol: string) => {
    const next = items.filter((item) => item.symbol !== symbol);
    setItems(next);
    writeWatchlist(next);
  };
  return (
    <>
      <header className="page-heading">
        <div className="eyebrow">Browser-local workspace</div>
        <h1>Watchlist</h1>
        <p className="muted">
          Assets saved on this device. Authentication and server persistence are
          not implemented.
        </p>
      </header>
      <div className="watch-toolbar">
        <input
          aria-label="Filter watchlist"
          className="search-input"
          placeholder="Filter saved assets…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </div>
      <div className="watch-table">
        {visible.length === 0 ? (
          <div className="empty-state">
            <h3>{items.length ? "No matches" : "Your watchlist is empty"}</h3>
            <p>Open an asset workspace and choose “Add to watchlist”.</p>
          </div>
        ) : (
          visible.map((item) => (
            <div className="watch-row" key={item.symbol}>
              <Link href={`/assets/${encodeURIComponent(item.symbol)}`}>
                <span className="ticker-symbol">{item.symbol}</span>
                <br />
                <span className="search-name">{item.name}</span>
              </Link>
              <span className="badge watch-secondary">{item.type}</span>
              <span className="faint watch-secondary">
                Open research workspace
              </span>
              <button
                className="button"
                onClick={() => remove(item.symbol)}
                type="button"
              >
                Remove
              </button>
            </div>
          ))
        )}
      </div>
    </>
  );
}
