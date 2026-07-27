import Link from "next/link";

const assets = [
  { symbol: "AAPL", name: "Apple Inc.", type: "Stock" },
  { symbol: "MSFT", name: "Microsoft Corp.", type: "Stock" },
  { symbol: "SPY", name: "SPDR S&P 500 ETF", type: "ETF" },
  { symbol: "XAUUSD", name: "Gold Spot / US Dollar", type: "Gold" },
];

export function ResearchDashboard() {
  return (
    <>
      <header className="page-heading">
        <div className="eyebrow">Research command center</div>
        <h1>Market intelligence</h1>
        <p className="muted">
          Explore normalized technical, asset, news, and surrounding-market
          evidence.
        </p>
      </header>
      <section className="ticker-strip" aria-label="Research shortcuts">
        {assets.map((asset) => (
          <Link
            className="ticker-card"
            href={`/assets/${asset.symbol}`}
            key={asset.symbol}
          >
            <div style={{ display: "flex", justifyContent: "space-between" }}>
              <span className="ticker-symbol">{asset.symbol}</span>
              <span className="badge">{asset.type}</span>
            </div>
            <div className="ticker-name">{asset.name}</div>
            <span className="workspace-link">Open research workspace →</span>
          </Link>
        ))}
      </section>
      <div className="grid two">
        <section className="panel">
          <div className="panel-header">
            <span className="panel-title">Intelligence layers</span>
            <span className="panel-meta">PHASES 2–7</span>
          </div>
          <div className="metric-grid">
            {[
              [
                "Technical intelligence",
                "Trend, momentum, volatility and levels",
              ],
              [
                "Technical assessment",
                "Deterministic score, confidence and risk",
              ],
              ["Asset intelligence", "Stock, ETF and gold-specific profiles"],
              [
                "News intelligence",
                "Grounded summaries and deterministic sentiment",
              ],
              [
                "Market context",
                "Aligned relative performance and surrounding markets",
              ],
            ].map(([label, note]) => (
              <div className="metric" key={label}>
                <div className="metric-value">{label}</div>
                <div className="metric-note">{note}</div>
              </div>
            ))}
          </div>
        </section>
        <section className="panel">
          <div className="panel-header">
            <span className="panel-title">Research principles</span>
          </div>
          <ul className="observation-list">
            <li className="factor">Provider-neutral normalized evidence</li>
            <li className="factor">
              Explicit freshness and missing-data states
            </li>
            <li className="factor">
              Transparent, versioned deterministic rules
            </li>
            <li className="factor">
              No BUY, SELL, HOLD, prediction, or execution
            </li>
          </ul>
        </section>
      </div>
    </>
  );
}
