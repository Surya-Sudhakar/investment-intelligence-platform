"use client";

import { useState } from "react";

import { useDebouncedValue } from "@/hooks/use-debounced-value";
import {
  useCandles,
  useProviderInformation,
  useQuote,
  useSymbolSearch,
} from "@/hooks/use-market-data";
import type { Interval } from "@/lib/api/market-data-types";

const intervals: Interval[] = ["5min", "15min", "1h", "1day"];

export function MarketDataScreen() {
  const [query, setQuery] = useState("");
  const [symbol, setSymbol] = useState("");
  const [interval, setInterval] = useState<Interval>("1day");
  const [limit, setLimit] = useState(20);
  const debouncedQuery = useDebouncedValue(query.trim(), 300);
  const search = useSymbolSearch(debouncedQuery);
  const candles = useCandles(symbol, interval, limit);
  const quote = useQuote(symbol);
  const { provider, health } = useProviderInformation();

  return (
    <section className="mt-12 border-t border-slate-300 pt-8">
      <h2 className="text-2xl font-semibold">Market-data test screen</h2>
      <p className="mt-2 text-sm text-slate-600">
        Provider data may be delayed, end-of-day, or cached. It is not labelled
        live.
      </p>
      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <div className="rounded border bg-white p-4">
          <h3 className="font-semibold">Provider</h3>
          {provider.isLoading && <p role="status">Loading provider…</p>}
          {provider.error && (
            <ErrorMessage
              message={provider.error.message}
              retry={() => void provider.refetch()}
            />
          )}
          {provider.data && (
            <>
              <p>{provider.data.provider_name}</p>
              <p className="text-sm">{provider.data.rate_limit_description}</p>
              <p className="text-sm">
                Intervals: {provider.data.supported_intervals.join(", ")}
              </p>
            </>
          )}
        </div>
        <div className="rounded border bg-white p-4">
          <h3 className="font-semibold">Provider health</h3>
          {health.isLoading && <p role="status">Checking provider…</p>}
          {health.error && (
            <ErrorMessage
              message={health.error.message}
              retry={() => void health.refetch()}
            />
          )}
          {health.data && (
            <p>
              {health.data.reachable ? "Reachable" : "Unavailable"} —{" "}
              {health.data.message}
            </p>
          )}
        </div>
      </div>
      <label className="mt-6 block font-medium" htmlFor="symbol-search">
        Search stocks
      </label>
      <input
        id="symbol-search"
        className="mt-2 w-full rounded border border-slate-300 bg-white p-2"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Apple or AAPL"
      />
      {query.trim().length === 1 && (
        <p className="mt-2 text-sm text-amber-700">
          Enter at least two characters.
        </p>
      )}
      {search.isFetching && <p role="status">Searching symbols…</p>}
      {search.error && <ErrorMessage message={search.error.message} />}
      {search.data?.length === 0 && <p>No stock symbols found.</p>}
      {search.data && search.data.length > 0 && (
        <ul className="mt-2 divide-y rounded border bg-white">
          {search.data.map((result) => (
            <li key={result.provider_symbol}>
              <button
                className="w-full p-3 text-left hover:bg-slate-50"
                onClick={() => setSymbol(result.symbol)}
              >
                <strong>{result.symbol}</strong> — {result.name}
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <label>
          <span className="block font-medium">Selected symbol</span>
          <input
            aria-label="Selected symbol"
            className="mt-2 w-full rounded border bg-white p-2"
            value={symbol}
            onChange={(event) => setSymbol(event.target.value.toUpperCase())}
          />
        </label>
        <label>
          <span className="block font-medium">Timeframe</span>
          <select
            className="mt-2 w-full rounded border bg-white p-2"
            value={interval}
            onChange={(event) => setInterval(event.target.value as Interval)}
          >
            {intervals.map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label>
          <span className="block font-medium">Candle limit</span>
          <select
            className="mt-2 w-full rounded border bg-white p-2"
            value={limit}
            onChange={(event) => setLimit(Number(event.target.value))}
          >
            {[10, 20, 50, 100].map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
      </div>
      <div className="mt-4 flex gap-3">
        <button
          className="rounded bg-blue-700 px-4 py-2 text-white disabled:opacity-50"
          disabled={!symbol || candles.isFetching}
          onClick={() => void candles.refetch()}
        >
          Load candles
        </button>
        <button
          className="rounded bg-slate-900 px-4 py-2 text-white disabled:opacity-50"
          disabled={!symbol || quote.isFetching}
          onClick={() => void quote.refetch()}
        >
          Latest quote
        </button>
      </div>
      {(candles.isFetching || quote.isFetching) && (
        <p role="status" className="mt-3">
          Loading market data…
        </p>
      )}
      {candles.error && (
        <ErrorMessage
          message={candles.error.message}
          retry={() => void candles.refetch()}
        />
      )}
      {quote.error && (
        <ErrorMessage
          message={quote.error.message}
          retry={() => void quote.refetch()}
        />
      )}
      {quote.data && (
        <div className="mt-6 rounded border bg-white p-4">
          <h3 className="font-semibold">Latest quote: {quote.data.symbol}</h3>
          <p>
            Price {quote.data.price}; status {quote.data.data_status}; source{" "}
            {new Date(quote.data.timestamp).toLocaleString()}
          </p>
        </div>
      )}
      {candles.data && candles.data.data.candles.length === 0 && (
        <p className="mt-6">No candles returned for this request.</p>
      )}
      {candles.data && candles.data.data.candles.length > 0 && (
        <div className="mt-6 overflow-x-auto">
          <p className="mb-2 text-sm">
            Accepted {candles.data.data.count} of{" "}
            {candles.data.data.received_count}; rejected{" "}
            {candles.data.data.rejected_count}. Status:{" "}
            {candles.data.data.data_status}.
          </p>
          <table className="w-full border-collapse bg-white text-sm">
            <thead>
              <tr>
                {["Time", "Open", "High", "Low", "Close", "Volume"].map(
                  (heading) => (
                    <th className="border p-2 text-left" key={heading}>
                      {heading}
                    </th>
                  ),
                )}
              </tr>
            </thead>
            <tbody>
              {candles.data.data.candles.map((candle) => (
                <tr key={candle.time}>
                  <td className="border p-2">{candle.time}</td>
                  <td className="border p-2">{candle.open}</td>
                  <td className="border p-2">{candle.high}</td>
                  <td className="border p-2">{candle.low}</td>
                  <td className="border p-2">{candle.close}</td>
                  <td className="border p-2">{candle.volume ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function ErrorMessage({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  return (
    <div role="alert" className="mt-3 rounded bg-red-50 p-3 text-red-800">
      {message}
      {retry && (
        <button className="ml-3 underline" onClick={retry}>
          Retry
        </button>
      )}
    </div>
  );
}
