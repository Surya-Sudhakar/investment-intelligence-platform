"use client";

import { FormEvent, useState } from "react";

import { useIntelligence } from "@/hooks/use-intelligence";

const formatNumber = (
  value: string | number | null | undefined,
  maximumFractionDigits = 2,
) => {
  if (value === null || value === undefined) return "Unavailable";
  const parsed = Number(value);
  return Number.isFinite(parsed)
    ? parsed.toLocaleString(undefined, { maximumFractionDigits })
    : "Unavailable";
};

export function IntelligenceDashboard() {
  const [input, setInput] = useState("AAPL");
  const [symbol, setSymbol] = useState("");
  const query = useIntelligence(symbol);

  function submit(event: FormEvent) {
    event.preventDefault();
    setSymbol(input.trim().toUpperCase());
  }

  const data = query.data;
  return (
    <section
      className="mt-12 border-t border-slate-300 pt-8"
      aria-labelledby="intelligence-title"
    >
      <p className="text-xs font-bold uppercase tracking-widest text-blue-700">
        Phase 3
      </p>
      <h2 id="intelligence-title" className="mt-2 text-2xl font-semibold">
        Market Intelligence
      </h2>
      <p className="mt-2 text-sm text-slate-600">
        Normalized observations only. This dashboard does not provide
        recommendations.
      </p>
      <form className="mt-6 flex gap-3" onSubmit={submit}>
        <label className="sr-only" htmlFor="intelligence-symbol">
          Stock symbol
        </label>
        <input
          id="intelligence-symbol"
          className="min-w-0 flex-1 rounded border border-slate-300 bg-white p-3"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Enter symbol, for example AAPL"
        />
        <button
          className="rounded bg-blue-700 px-5 py-3 font-medium text-white disabled:opacity-50"
          disabled={!input.trim() || query.isFetching}
        >
          Analyze
        </button>
      </form>
      {query.isFetching && (
        <p className="mt-4" role="status">
          Loading intelligence…
        </p>
      )}
      {query.error && (
        <div className="mt-4 rounded bg-red-50 p-4 text-red-800" role="alert">
          {query.data
            ? `Latest refresh failed; showing the previous snapshot. ${query.error.message}`
            : query.error.message}
          <button
            className="ml-3 underline"
            onClick={() => void query.refetch()}
          >
            Retry
          </button>
        </div>
      )}
      {data && (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card label="Quote" value={formatNumber(data.quote.price)} />
            <Card
              label="Market status"
              value={data.market_status.state}
              detail={data.market_status.reason}
            />
            <Card
              label="Freshness"
              value={data.freshness.state}
              detail={data.freshness.reason}
            />
            <Card label="Provider" value={data.provider} />
          </div>
          <h3 className="mt-8 text-lg font-semibold">Classification</h3>
          <div className="mt-3 grid gap-4 sm:grid-cols-3">
            <Card label="Trend" value={data.trend} />
            <Card label="Momentum" value={data.momentum} />
            <Card label="Volatility" value={data.volatility} />
          </div>
          <h3 className="mt-8 text-lg font-semibold">Indicators</h3>
          <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card label="EMA 20" value={formatNumber(data.indicators.ema20)} />
            <Card label="EMA 50" value={formatNumber(data.indicators.ema50)} />
            <Card label="RSI 14" value={formatNumber(data.indicators.rsi14)} />
            <Card label="ATR 14" value={formatNumber(data.indicators.atr14)} />
            <Card
              label="Average volume"
              value={formatNumber(data.indicators.average_volume, 0)}
            />
            <Card
              label="52-week high"
              value={formatNumber(data.indicators.high_52_week)}
            />
            <Card
              label="52-week low"
              value={formatNumber(data.indicators.low_52_week)}
            />
            <Card
              label="Daily change %"
              value={formatNumber(data.indicators.daily_change_percentage)}
            />
          </div>
          <h3 className="mt-8 text-lg font-semibold">Levels</h3>
          <div className="mt-3 grid gap-4 sm:grid-cols-2">
            <Card
              label="Nearest support"
              value={formatNumber(data.support_resistance.nearest_support)}
              detail={`Distance: ${formatNumber(data.support_resistance.distance_to_support_percentage)}%`}
            />
            <Card
              label="Nearest resistance"
              value={formatNumber(data.support_resistance.nearest_resistance)}
              detail={`Distance: ${formatNumber(data.support_resistance.distance_to_resistance_percentage)}%`}
            />
          </div>
          <p className="mt-5 text-xs text-slate-500">
            Snapshot timestamp: {new Date(data.timestamp).toLocaleString()}.
            Auto-refreshes every four hours while the provider is available.
          </p>
        </>
      )}
    </section>
  );
}

function Card({
  label,
  value,
  detail,
}: {
  label: string;
  value: string | number;
  detail?: string;
}) {
  return (
    <article className="rounded border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className="mt-2 break-words font-semibold">{value}</p>
      {detail && <p className="mt-2 text-xs text-slate-500">{detail}</p>}
    </article>
  );
}
