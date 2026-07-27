"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { useAssessment } from "@/hooks/use-assessment";
import { useAssetIntelligence } from "@/hooks/use-asset-intelligence";
import { useIntelligence } from "@/hooks/use-intelligence";
import { useMarketContext } from "@/hooks/use-market-context";
import { useNewsIntelligence } from "@/hooks/use-news-intelligence";
import { marketDataApi } from "@/lib/api/market-data";
import { addWatchItem } from "@/lib/watchlist";

type Tab =
  | "overview"
  | "chart"
  | "technicals"
  | "assessment"
  | "profile"
  | "news"
  | "context";

function display(value: unknown): string {
  if (value === null || value === undefined || value === "")
    return "Unavailable";
  if (typeof value === "number") return value.toLocaleString();
  if (typeof value === "string") return value.replaceAll("_", " ");
  return JSON.stringify(value);
}

function Metric({
  label,
  value,
  note,
}: {
  label: string;
  value: unknown;
  note?: string;
}) {
  return (
    <div className="metric">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{display(value)}</div>
      {note && <div className="metric-note">{note}</div>}
    </div>
  );
}

function PriceChart({ symbol }: { symbol: string }) {
  const candles = useQuery({
    queryKey: ["workspace-candles", symbol, "1day", 60],
    queryFn: ({ signal }) => marketDataApi.candles(symbol, "1day", 60, signal),
    retry: false,
  });
  const points = useMemo(() => {
    const values =
      candles.data?.data.candles
        .map((item) => Number(item.close))
        .filter(Number.isFinite) ?? [];
    if (values.length < 2) return "";
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    return values
      .map(
        (value, index) =>
          `${(index / (values.length - 1)) * 100},${95 - ((value - min) / range) * 85}`,
      )
      .join(" ");
  }, [candles.data]);
  if (candles.isLoading)
    return (
      <div className="chart-empty">
        <div className="loading-bar" style={{ width: "50%" }} />
      </div>
    );
  if (!points)
    return (
      <div className="chart-empty">Daily candle history is unavailable.</div>
    );
  return (
    <svg
      className="chart"
      preserveAspectRatio="none"
      viewBox="0 0 100 100"
      role="img"
      aria-label={`${symbol} daily price chart`}
    >
      <defs>
        <linearGradient id="chart-fill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="currentColor" stopOpacity=".25" />
          <stop offset="1" stopColor="currentColor" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polyline
        fill="none"
        points={points}
        stroke="currentColor"
        strokeWidth="1.6"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

export function AssetWorkspace({ symbol }: { symbol: string }) {
  const [tab, setTab] = useState<Tab>("overview");
  const [watchlistMessage, setWatchlistMessage] = useState("");
  const intelligence = useIntelligence(symbol);
  const assessment = useAssessment(symbol);
  const asset = useAssetIntelligence(symbol);
  const news = useNewsIntelligence(symbol);
  const context = useMarketContext(symbol);
  const quote = intelligence.data?.quote;
  const isLoading = [intelligence, assessment, asset, news, context].some(
    (query) => query.isLoading,
  );
  const errors = [intelligence, assessment, asset, news, context].filter(
    (query) => query.isError,
  ).length;

  const addToWatchlist = () => {
    const added = addWatchItem({
      symbol,
      name: asset.data?.display_name ?? symbol,
      type: asset.data?.asset_type ?? "UNKNOWN",
    });
    setWatchlistMessage(added ? "Added to watchlist" : "Already in watchlist");
  };

  return (
    <>
      {isLoading && (
        <div className="loading-bar" style={{ marginBottom: 18 }} />
      )}
      {errors > 0 && (
        <div className="notice error-notice">
          {errors} intelligence layer{errors === 1 ? "" : "s"} could not be
          loaded. Available layers remain visible.
        </div>
      )}
      <div className="workspace-header">
        <div className="asset-identity">
          <span className="asset-glyph">{symbol.slice(0, 2)}</span>
          <div>
            <div className="asset-symbol">{symbol}</div>
            <div className="asset-name">
              {asset.data?.display_name ?? "Loading normalized asset identity…"}
            </div>
            <span className="badge">{asset.data?.asset_type ?? "ASSET"}</span>{" "}
            {asset.data?.exchange && (
              <span className="badge">{asset.data.exchange}</span>
            )}
          </div>
        </div>
        <div className="price-block">
          <div className="asset-price">
            {asset.data?.currency ?? ""}{" "}
            {quote ? Number(quote.price).toLocaleString() : "—"}
          </div>
          <div
            className={`asset-change ${Number(quote?.change_percentage ?? 0) >= 0 ? "positive" : "negative"}`}
          >
            {quote?.change_percentage
              ? `${Number(quote.change_percentage) >= 0 ? "+" : ""}${quote.change_percentage}%`
              : "Change unavailable"}
          </div>
          <div className="panel-meta">
            {quote?.data_status ?? "UNKNOWN"} ·{" "}
            {quote?.provider ?? asset.data?.provider ?? "provider unavailable"}
          </div>
          <div className="actions">
            <button className="button" onClick={addToWatchlist} type="button">
              ☆ Add to watchlist
            </button>
            <span aria-live="polite" className="panel-meta">
              {watchlistMessage}
            </span>
          </div>
        </div>
      </div>
      <nav className="tabs" aria-label="Workspace sections">
        {(
          [
            "overview",
            "chart",
            "technicals",
            "assessment",
            "profile",
            "news",
            "context",
          ] as Tab[]
        ).map((item) => (
          <button
            className={`tab ${tab === item ? "active" : ""}`}
            key={item}
            onClick={() => setTab(item)}
            type="button"
          >
            {item.charAt(0).toUpperCase() + item.slice(1)}
          </button>
        ))}
      </nav>

      {(tab === "overview" || tab === "chart") && (
        <section className="panel">
          <div className="panel-header">
            <span className="panel-title">Daily price history</span>
            <span className="panel-meta">1DAY · NORMALIZED</span>
          </div>
          <PriceChart symbol={symbol} />
        </section>
      )}

      {(tab === "overview" || tab === "technicals") && (
        <section className="panel">
          <div className="panel-header">
            <span className="panel-title">Technical intelligence</span>
            <span className="panel-meta">
              {intelligence.data?.timestamp
                ? new Date(intelligence.data.timestamp).toLocaleString()
                : "Awaiting snapshot"}
            </span>
          </div>
          <div className="metric-grid">
            <Metric label="Trend" value={intelligence.data?.trend} />
            <Metric label="Momentum" value={intelligence.data?.momentum} />
            <Metric label="Volatility" value={intelligence.data?.volatility} />
            <Metric
              label="RSI 14"
              value={intelligence.data?.indicators.rsi14}
            />
            <Metric
              label="EMA 20"
              value={intelligence.data?.indicators.ema20}
            />
            <Metric
              label="EMA 50"
              value={intelligence.data?.indicators.ema50}
            />
            <Metric
              label="Support"
              value={intelligence.data?.support_resistance.nearest_support}
            />
            <Metric
              label="Resistance"
              value={intelligence.data?.support_resistance.nearest_resistance}
            />
          </div>
        </section>
      )}

      {(tab === "overview" || tab === "assessment") && (
        <section className="panel">
          <div className="panel-header">
            <span className="panel-title">Technical assessment</span>
            <span className="panel-meta">
              {assessment.data?.scoring_version ?? "technical-v1"}
            </span>
          </div>
          <div className="metric-grid">
            <Metric label="Outlook" value={assessment.data?.assessment} />
            <Metric
              label="Technical score"
              value={assessment.data?.technical_score}
            />
            <Metric
              label="Confidence"
              value={assessment.data?.confidence_score}
            />
            <Metric
              label="Independent risk"
              value={
                assessment.data
                  ? `${assessment.data.risk.level} · ${assessment.data.risk.score}`
                  : null
              }
            />
          </div>
          {assessment.data && (
            <>
              <div className="progress">
                <span
                  style={{ width: `${assessment.data.technical_score}%` }}
                />
              </div>
              <ul className="factor-list" style={{ marginTop: 14 }}>
                {assessment.data.supporting_factors
                  .slice(0, tab === "overview" ? 3 : undefined)
                  .map((factor) => (
                    <li className="factor" key={factor.code}>
                      {factor.message}
                    </li>
                  ))}
              </ul>
            </>
          )}
        </section>
      )}

      {(tab === "overview" || tab === "profile") && (
        <section className="panel">
          <div className="panel-header">
            <span className="panel-title">
              {asset.data?.asset_type === "ETF"
                ? "Fund intelligence"
                : asset.data?.asset_type === "GOLD"
                  ? "Commodity intelligence"
                  : "Asset intelligence"}
            </span>
            <span className="panel-meta">{asset.data?.provider}</span>
          </div>
          {asset.data?.warnings.map((warning) => (
            <div className="notice" key={warning}>
              {warning}
            </div>
          ))}
          <div className="metric-grid">
            {Object.entries(asset.data?.profile ?? {})
              .slice(0, 8)
              .map(([key, value]) => (
                <Metric key={key} label={key} value={value} />
              ))}
            {Object.entries(asset.data?.metrics ?? {})
              .slice(0, 8)
              .map(([key, value]) => (
                <Metric key={key} label={key} value={value} />
              ))}
          </div>
        </section>
      )}

      {(tab === "overview" || tab === "news") && (
        <section className="panel">
          <div className="panel-header">
            <span className="panel-title">News intelligence</span>
            <span className="panel-meta">
              {news.data
                ? `${news.data.aggregate.overall_sentiment} · ${news.data.aggregate.confidence}% confidence`
                : "Awaiting coverage"}
            </span>
          </div>
          {news.data?.warnings.map((warning) => (
            <div className="notice" key={warning}>
              {warning}
            </div>
          ))}
          {news.data?.summary && (
            <p className="muted" style={{ lineHeight: 1.6 }}>
              {news.data.summary}
            </p>
          )}
          <div className="news-list">
            {news.data?.articles
              .slice(0, tab === "overview" ? 3 : undefined)
              .map((article) => (
                <article className="news-row" key={article.id}>
                  <a href={article.url} rel="noreferrer" target="_blank">
                    {article.title}
                  </a>
                  <div className="news-meta">
                    <span>{article.source}</span>
                    <span>{article.sentiment}</span>
                    <span>
                      {new Date(article.published_at).toLocaleDateString()}
                    </span>
                  </div>
                </article>
              ))}
          </div>
          {!news.isLoading && !news.data?.articles.length && (
            <div className="empty-state">
              No provider news is available for this asset.
            </div>
          )}
        </section>
      )}

      {(tab === "overview" || tab === "context") && (
        <section className="panel">
          <div className="panel-header">
            <span className="panel-title">Market context</span>
            <span className="panel-meta">
              {context.data?.methodology_version ?? "market-context-v1"}
            </span>
          </div>
          {context.data?.warnings.map((warning) => (
            <div className="notice" key={warning}>
              {warning}
            </div>
          ))}
          <div className="metric-grid">
            <Metric
              label="Overall context"
              value={context.data?.overall_context.value}
              note={context.data?.overall_context.reason}
            />
            <Metric label="Confidence" value={context.data?.confidence} />
            <Metric
              label="Data status"
              value={context.data?.partial_data_status}
            />
            <Metric label="Freshness" value={context.data?.freshness.state} />
          </div>
          <ul className="observation-list" style={{ marginTop: 14 }}>
            {context.data?.supporting_observations
              .slice(0, tab === "overview" ? 3 : undefined)
              .map((item) => (
                <li className="factor" key={item}>
                  {item}
                </li>
              ))}
          </ul>
        </section>
      )}
    </>
  );
}
