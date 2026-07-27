"use client";

import { FormEvent, useState } from "react";

import { useMarketContext } from "@/hooks/use-market-context";
import type {
  AvailabilityStatus,
  AvailableValue,
  MarketContext,
} from "@/lib/api/market-context-types";

const label = (value: string) =>
  value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

const statusLabel: Record<AvailabilityStatus, string> = {
  available: "Available",
  unavailable: "Unavailable",
  not_applicable: "Not applicable",
  planned_phase8: "Planned for Phase 8",
};

function display(value: unknown): string {
  if (value === null || value === undefined || value === "")
    return "Unavailable";
  if (typeof value === "string" || typeof value === "number")
    return String(value);
  if (Array.isArray(value))
    return value.length ? value.join(", ") : "Unavailable";
  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    if (typeof record.classification === "string") {
      const difference = record.difference_percentage_points;
      const performance = record.return_percentage;
      if (difference !== undefined)
        return `${label(record.classification)} (${difference} pp)`;
      if (performance !== undefined)
        return `${label(record.classification)} (${performance}%)`;
      return label(record.classification);
    }
    if (typeof record.name === "string") {
      return `${record.name}${record.is_proxy ? " (proxy)" : ""}`;
    }
  }
  return "Available";
}

export function MarketContextDashboard() {
  const [input, setInput] = useState("AAPL");
  const [symbol, setSymbol] = useState("");
  const query = useMarketContext(symbol);

  function submit(event: FormEvent) {
    event.preventDefault();
    setSymbol(input.trim().toUpperCase().replace("/", ""));
  }

  return (
    <section
      className="mt-12 border-t border-slate-300 pt-8"
      aria-labelledby="market-context-title"
    >
      <p className="text-xs font-bold uppercase tracking-widest text-blue-700">
        Phase 7
      </p>
      <h2 id="market-context-title" className="mt-2 text-2xl font-semibold">
        Market Context
      </h2>
      <p className="mt-2 text-sm text-slate-600">
        Deterministic comparison with the surrounding market. No investment
        recommendation is produced.
      </p>
      <form className="mt-6 flex gap-3" onSubmit={submit}>
        <label className="sr-only" htmlFor="market-context-symbol">
          Asset symbol
        </label>
        <input
          id="market-context-symbol"
          className="min-w-0 flex-1 rounded border border-slate-300 bg-white p-3"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="AAPL, QQQ, or XAUUSD"
        />
        <button
          className="rounded bg-blue-700 px-5 py-3 font-medium text-white disabled:opacity-50"
          disabled={!input.trim() || query.isFetching}
        >
          Load context
        </button>
      </form>
      {query.isFetching && (
        <p className="mt-4" role="status">
          Loading market context…
        </p>
      )}
      {query.error && (
        <div className="mt-4 rounded bg-red-50 p-4 text-red-800" role="alert">
          {query.error.message}
          <button
            className="ml-3 underline"
            onClick={() => void query.refetch()}
          >
            Retry
          </button>
        </div>
      )}
      {query.data && <ContextResult data={query.data} />}
    </section>
  );
}

function ContextResult({ data }: { data: MarketContext }) {
  return (
    <>
      {data.warnings.length > 0 && (
        <div className="mt-5 rounded bg-amber-50 p-4 text-sm text-amber-900">
          <p className="font-semibold">Partial or limited data</p>
          <ul className="mt-2 list-disc pl-5">
            {data.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card
          title="Overall context"
          value={renderField(data.overall_context)}
        />
        <Card title="Confidence" value={`${data.confidence}%`} />
        <Card title="Asset type" value={data.asset_type} />
        <Card
          title="Freshness"
          value={data.freshness.state ?? statusLabel[data.freshness.status]}
        />
      </div>
      <ContextSection title="Market" values={data.market} />
      {data.asset_type === "STOCK" && (
        <>
          <ContextSection title="Sector" values={data.sector} />
          <ContextSection title="Industry" values={data.industry} />
        </>
      )}
      {data.asset_type === "GOLD" && (
        <ContextSection title="Commodity context" values={data.commodity} />
      )}
      {data.asset_type === "ETF" && (
        <ContextSection title="ETF context" values={data.etf} />
      )}
      <ContextSection
        title="Relative strength"
        values={data.relative_strength}
      />
      <h3 className="mt-8 text-lg font-semibold">Supporting observations</h3>
      {data.supporting_observations.length ? (
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-700">
          {data.supporting_observations.map((observation) => (
            <li key={observation}>{observation}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-sm text-slate-600">
          No supporting observations are available.
        </p>
      )}
      <p className="mt-5 text-xs text-slate-500">
        {data.methodology_version}; {data.horizon.lookback_sessions} daily
        sessions. Generated {new Date(data.generated_at).toLocaleString()}.
      </p>
    </>
  );
}

function renderField(value: AvailableValue<unknown>): string {
  const alignment = value.alignment;
  const alignmentText = alignment
    ? alignment.alignment_sufficient
      ? ` — ${alignment.actual_overlap_count} aligned daily observations`
      : ` — ${alignment.actual_overlap_count} common observations; ${alignment.minimum_required} required`
    : "";
  return value.status === "available"
    ? `${display(value.value)}${alignmentText}`
    : `${statusLabel[value.status]} — ${value.reason}${alignmentText}`;
}

function ContextSection({
  title,
  values,
}: {
  title: string;
  values: Record<string, AvailableValue<unknown>>;
}) {
  return (
    <>
      <h3 className="mt-8 text-lg font-semibold">{title}</h3>
      <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Object.entries(values).map(([key, value]) => (
          <Card key={key} title={label(key)} value={renderField(value)} />
        ))}
      </div>
    </>
  );
}

function Card({ title, value }: { title: string; value: string }) {
  return (
    <article className="rounded border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {title}
      </p>
      <p className="mt-2 break-words font-semibold">{value}</p>
    </article>
  );
}
