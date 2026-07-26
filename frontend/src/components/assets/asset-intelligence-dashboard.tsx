"use client";

import { FormEvent, useState } from "react";

import { useAssetIntelligence } from "@/hooks/use-asset-intelligence";
import type { AssetIntelligence } from "@/lib/api/asset-intelligence-types";

const label = (value: string) =>
  value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

const display = (value: unknown): string => {
  if (value === null || value === undefined || value === "")
    return "Unavailable";
  if (typeof value === "number") return value.toLocaleString();
  if (typeof value === "string") {
    const number = Number(value);
    return Number.isFinite(number) && value.trim() !== ""
      ? number.toLocaleString(undefined, { maximumFractionDigits: 2 })
      : value;
  }
  if (Array.isArray(value)) {
    if (!value.length) return "Unavailable";
    return value
      .map((item): string => {
        if (typeof item !== "object" || item === null) return String(item);
        const record = item as Record<string, unknown>;
        const name: string = display(record.name);
        const weight = record.weight_percentage;
        return weight === null || weight === undefined
          ? name
          : `${name} (${display(weight)}%)`;
      })
      .join(", ");
  }
  return "Available";
};

export function AssetIntelligenceDashboard() {
  const [input, setInput] = useState("AAPL");
  const [symbol, setSymbol] = useState("");
  const query = useAssetIntelligence(symbol);

  function submit(event: FormEvent) {
    event.preventDefault();
    setSymbol(input.trim().toUpperCase().replace("/", ""));
  }

  return (
    <section
      className="mt-12 border-t border-slate-300 pt-8"
      aria-labelledby="asset-intelligence-title"
    >
      <p className="text-xs font-bold uppercase tracking-widest text-blue-700">
        Phase 5
      </p>
      <h2 id="asset-intelligence-title" className="mt-2 text-2xl font-semibold">
        Asset Intelligence
      </h2>
      <p className="mt-2 text-sm text-slate-600">
        Provider-neutral profiles and asset-specific observations. No investment
        recommendation is produced.
      </p>
      <form className="mt-6 flex gap-3" onSubmit={submit}>
        <label className="sr-only" htmlFor="asset-symbol">
          Asset symbol
        </label>
        <input
          id="asset-symbol"
          className="min-w-0 flex-1 rounded border border-slate-300 bg-white p-3"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="AAPL, GLD, or XAUUSD"
        />
        <button
          className="rounded bg-blue-700 px-5 py-3 font-medium text-white disabled:opacity-50"
          disabled={!input.trim() || query.isFetching}
        >
          Inspect
        </button>
      </form>
      {query.isFetching && (
        <p className="mt-4" role="status">
          Loading asset intelligence…
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
      {query.data && <AssetResult data={query.data} />}
    </section>
  );
}

function AssetResult({ data }: { data: AssetIntelligence }) {
  return (
    <>
      {data.warnings.length > 0 && (
        <div
          className="mt-5 rounded bg-amber-50 p-4 text-sm text-amber-900"
          role="status"
        >
          <p className="font-semibold">Partial or limited data</p>
          <ul className="mt-2 list-disc pl-5">
            {data.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </div>
      )}
      {data.freshness?.state === "STALE" && (
        <p className="mt-4 rounded bg-amber-50 p-4 text-amber-900">
          This market observation is stale.
        </p>
      )}
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card title="Asset" value={data.display_name ?? data.symbol} />
        <Card title="Asset type" value={data.asset_type} />
        <Card title="Exchange" value={display(data.exchange)} />
        <Card title="Provider" value={data.provider} />
      </div>
      {data.asset_type === "STOCK" && (
        <>
          <RecordSection title="Company profile" values={data.profile} />
          <RecordSection title="Key financial metrics" values={data.metrics} />
          <RecordSection
            title="Fundamental condition"
            values={data.classification}
          />
        </>
      )}
      {data.asset_type === "GOLD" && (
        <>
          <RecordSection title="Gold instrument" values={data.profile} />
          <RecordSection
            title="Gold market observations"
            values={data.metrics}
          />
        </>
      )}
      {data.asset_type === "ETF" && (
        <>
          <RecordSection title="Fund profile" values={data.profile} />
          <RecordSection
            title="Fund metrics and allocations"
            values={data.metrics}
          />
        </>
      )}
      <p className="mt-5 text-xs text-slate-500">
        Generated {new Date(data.generated_at).toLocaleString()}.
      </p>
    </>
  );
}

function RecordSection({
  title,
  values,
}: {
  title: string;
  values: Record<string, unknown> | null;
}) {
  const entries = values ? Object.entries(values) : [];
  return (
    <>
      <h3 className="mt-8 text-lg font-semibold">{title}</h3>
      <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {entries.length ? (
          entries.map(([key, value]) => (
            <Card key={key} title={label(key)} value={display(value)} />
          ))
        ) : (
          <Card title="Availability" value="Unavailable" />
        )}
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
