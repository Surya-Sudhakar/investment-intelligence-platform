"use client";

import { FormEvent, useState } from "react";

import { useAssessment } from "@/hooks/use-assessment";
import type { AssessmentFactor } from "@/lib/api/assessment-types";

export function AssessmentDashboard() {
  const [input, setInput] = useState("AAPL");
  const [symbol, setSymbol] = useState("");
  const query = useAssessment(symbol);
  const data = query.data;

  function submit(event: FormEvent) {
    event.preventDefault();
    setSymbol(input.trim().toUpperCase());
  }

  return (
    <section
      className="mt-12 border-t border-slate-300 pt-8"
      aria-labelledby="assessment-title"
    >
      <p className="text-xs font-bold uppercase tracking-widest text-blue-700">
        Phase 4A
      </p>
      <h2 id="assessment-title" className="mt-2 text-2xl font-semibold">
        Technical Assessment
      </h2>
      <p className="mt-2 text-sm text-slate-600">
        Deterministic daily technical decision support based only on the
        normalized Phase 3 snapshot.
      </p>
      <form className="mt-6 flex gap-3" onSubmit={submit}>
        <label className="sr-only" htmlFor="assessment-symbol">
          Stock symbol
        </label>
        <input
          id="assessment-symbol"
          className="min-w-0 flex-1 rounded border border-slate-300 bg-white p-3"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Enter symbol, for example AAPL"
        />
        <button
          className="rounded bg-blue-700 px-5 py-3 font-medium text-white disabled:opacity-50"
          disabled={!input.trim() || query.isFetching}
        >
          Assess
        </button>
      </form>
      {query.isFetching && <p className="mt-4">Generating assessment…</p>}
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
      {data && (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="Outlook" value={data.assessment} />
            <Metric
              label="Technical score"
              value={`${data.technical_score}/100`}
            />
            <Metric label="Confidence" value={`${data.confidence_score}/100`} />
            <Metric
              label="Risk"
              value={`${data.risk.level} · ${data.risk.score}/100`}
            />
          </div>
          <p className="mt-4 text-sm text-slate-600">
            Horizon: {data.time_horizon.replace("_", " ")} · Interval:{" "}
            {data.interval} · Method: {data.scoring_version}
          </p>
          <div className="mt-8 grid gap-6 sm:grid-cols-2">
            <FactorList
              title="Supporting factors"
              items={data.supporting_factors}
            />
            <FactorList
              title="Conflicting factors"
              items={data.conflicting_factors}
            />
            <FactorList title="Risk factors" items={data.risk_factors} />
            <FactorList
              title="Missing-data factors"
              items={data.missing_data_factors}
            />
          </div>
          <h3 className="mt-8 text-lg font-semibold">Component scoring</h3>
          <div className="mt-3 overflow-x-auto rounded border border-slate-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="p-3">Component</th>
                  <th className="p-3">Weight</th>
                  <th className="p-3">Input</th>
                  <th className="p-3">Signal</th>
                </tr>
              </thead>
              <tbody>
                {data.components.map((component) => (
                  <tr
                    className="border-t border-slate-200"
                    key={component.name}
                  >
                    <td className="p-3">
                      <strong>{component.name.replaceAll("_", " ")}</strong>
                      <span className="mt-1 block text-xs text-slate-500">
                        {component.explanation}
                      </span>
                    </td>
                    <td className="p-3">{component.weight}</td>
                    <td className="p-3">
                      {component.raw_value ?? "Unavailable"}
                    </td>
                    <td className="p-3">{component.signal ?? "Unavailable"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <h3 className="mt-8 text-lg font-semibold">Data quality</h3>
          <div className="mt-3 grid gap-4 sm:grid-cols-3">
            <Metric
              label="Input coverage"
              value={`${data.data_quality.input_coverage_percentage}%`}
            />
            <Metric
              label="Freshness"
              value={data.data_quality.freshness_state}
            />
            <Metric
              label="Market status"
              value={data.data_quality.market_status}
            />
          </div>
          <p className="mt-5 text-xs text-slate-500">
            Snapshot: {new Date(data.snapshot_timestamp).toLocaleString()} ·
            Generated: {new Date(data.generated_at).toLocaleString()}
          </p>
          <p className="mt-3 text-xs text-slate-500">
            RSI overbought and oversold values express directional momentum and
            extension risk; they are not automatic reversal conditions.
          </p>
        </>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className="mt-2 break-words font-semibold">{value}</p>
    </article>
  );
}

function FactorList({
  title,
  items,
}: {
  title: string;
  items: AssessmentFactor[];
}) {
  return (
    <div>
      <h3 className="font-semibold">{title}</h3>
      {items.length ? (
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
          {items.map((item) => (
            <li key={`${item.code}-${item.message}`}>{item.message}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-sm text-slate-500">None identified.</p>
      )}
    </div>
  );
}
