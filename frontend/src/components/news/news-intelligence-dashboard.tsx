"use client";

import { FormEvent, useState } from "react";
import { useNewsIntelligence } from "@/hooks/use-news-intelligence";

export function NewsIntelligenceDashboard() {
  const [input, setInput] = useState("AAPL");
  const [symbol, setSymbol] = useState("");
  const query = useNewsIntelligence(symbol);
  const data = query.data;
  function submit(event: FormEvent) {
    event.preventDefault();
    setSymbol(input.trim().toUpperCase().replace("/", ""));
  }
  return (
    <section
      className="mt-12 border-t border-slate-300 pt-8"
      aria-labelledby="news-title"
    >
      <p className="text-xs font-bold uppercase tracking-widest text-blue-700">
        Phase 6
      </p>
      <h2 id="news-title" className="mt-2 text-2xl font-semibold">
        News Intelligence
      </h2>
      <p className="mt-2 text-sm text-slate-600">
        Grounded news summaries and deterministic sentiment. No investment
        recommendation.
      </p>
      <form className="mt-6 flex gap-3" onSubmit={submit}>
        <label className="sr-only" htmlFor="news-symbol">
          Asset symbol
        </label>
        <input
          id="news-symbol"
          className="min-w-0 flex-1 rounded border border-slate-300 bg-white p-3"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="AAPL, GLD, or XAUUSD"
        />
        <button
          className="rounded bg-blue-700 px-5 py-3 font-medium text-white disabled:opacity-50"
          disabled={!input.trim() || query.isFetching}
        >
          Load news
        </button>
      </form>
      {query.isFetching && (
        <p className="mt-4" role="status">
          Loading news intelligence…
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
      {data && (
        <>
          {data.warnings.length > 0 && (
            <div
              className="mt-4 rounded bg-amber-50 p-4 text-amber-900"
              role="status"
            >
              {data.warnings.join(" ")}
            </div>
          )}
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <Card
              label="Overall sentiment"
              value={data.aggregate.overall_sentiment}
            />
            <Card label="Confidence" value={`${data.aggregate.confidence}%`} />
            <Card label="Freshness" value={data.freshness.state} />
          </div>
          <h3 className="mt-8 text-lg font-semibold">News Summary</h3>
          <p className="mt-3 rounded border bg-white p-4">{data.summary}</p>
          {data.groups.length > 0 && (
            <>
              <h3 className="mt-8 text-lg font-semibold">Grouped Stories</h3>
              <div className="mt-3 grid gap-4">
                {data.groups.map((group) => (
                  <article
                    key={group.id}
                    className="rounded border bg-white p-4"
                  >
                    <p className="font-semibold">{group.title}</p>
                    <p className="mt-2 text-sm text-slate-600">
                      {group.summary}
                    </p>
                    <p className="mt-2 text-xs">
                      {group.article_count} article(s) · {group.sentiment}
                    </p>
                  </article>
                ))}
              </div>
            </>
          )}
          <h3 className="mt-8 text-lg font-semibold">Recent News</h3>
          {data.articles.length === 0 ? (
            <p className="mt-3 rounded border bg-white p-4">
              No recent news available.
            </p>
          ) : (
            <div className="mt-3 grid gap-4">
              {data.articles.map((article) => (
                <article
                  key={article.id}
                  className="rounded border bg-white p-4"
                >
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-semibold text-blue-700 underline"
                  >
                    {article.title}
                  </a>
                  <p className="mt-2 text-sm">{article.summary}</p>
                  <p className="mt-2 text-xs text-slate-500">
                    {article.source} ·{" "}
                    {new Date(article.published_at).toLocaleString()} ·{" "}
                    {article.sentiment} · {article.freshness.state}
                  </p>
                </article>
              ))}
            </div>
          )}
        </>
      )}
    </section>
  );
}

function Card({ label, value }: { label: string; value: string }) {
  return (
    <article className="rounded border bg-white p-4 shadow-sm">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="mt-2 font-semibold">{value}</p>
    </article>
  );
}
