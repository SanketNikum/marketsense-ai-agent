import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

function PriceChange({ value }) {
  const isUp = value >= 0;
  return (
    <span style={{ ...s.badge, ...(isUp ? s.badgeUp : s.badgeDown) }}>
      {isUp ? "▲" : "▼"} {Math.abs(value).toFixed(2)}%
    </span>
  );
}

function StoryCard({ story, mover }) {
  return (
    <article style={s.storyCard}>
      <div style={s.storyCardHeader}>
        <h3 style={s.ticker}>{story.ticker}</h3>
        {mover && <PriceChange value={mover.pct_change} />}
      </div>
      <p style={s.storyText}>{story.story}</p>
      <div style={s.storyFooter}>AI-generated · grounded in retrieved context</div>
    </article>
  );
}

function MoverRow({ mover }) {
  return (
    <tr>
      <td style={s.td}><strong>{mover.ticker}</strong></td>
      <td style={s.td}>₹{mover.close.toLocaleString("en-IN")}</td>
      <td style={s.td}><PriceChange value={mover.pct_change} /></td>
      <td style={{ ...s.td, color: "var(--text-muted)" }}>{mover.volume.toLocaleString("en-IN")}</td>
      <td style={s.td}>
        {mover.worth_story ? (
          <span style={{ ...s.pill, ...s.pillYes }}>story written</span>
        ) : (
          <span style={{ ...s.pill, ...s.pillNo }}>below threshold</span>
        )}
      </td>
    </tr>
  );
}

function LoadingSkeleton() {
  return (
    <div style={s.card}>
      <div style={{ ...s.skeletonLine, width: "40%" }} />
      <div style={{ ...s.skeletonLine, width: "90%" }} />
      <div style={{ ...s.skeletonLine, width: "75%" }} />
    </div>
  );
}

export default function Home() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/stories`)
      .then((res) => res.json())
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  const moversByTicker = {};
  if (data) {
    for (const m of data.classified_movers) moversByTicker[m.ticker] = m;
  }

  return (
    <div style={s.page}>
      <header style={s.header}>
        <div style={s.headerInner}>
          <div>
            <h1 style={s.title}>MarketSense</h1>
            <p style={s.subtitle}>AI-generated daily market explainers, grounded in real data</p>
          </div>
          <div style={s.dateBadge}>{new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" })}</div>
        </div>
      </header>

      <main style={s.main}>
        <section>
          <h2 style={s.sectionTitle}>Today&apos;s Stories</h2>

          {error && <div style={s.errorBox}>Couldn&apos;t reach the API: {error}</div>}

          {!data && !error && (
            <>
              <LoadingSkeleton />
              <LoadingSkeleton />
            </>
          )}

          {data && data.stories.length === 0 && (
            <div style={s.emptyState}>
              <div style={s.emptyIcon}>📈</div>
              <p style={{ margin: 0, fontWeight: 600 }}>No significant moves worth a story today</p>
              <p style={{ margin: "0.25rem 0 0", color: "var(--text-muted)", fontSize: "0.9rem" }}>
                The classifier reviews every tracked stock and only writes when a move clears its bar.
              </p>
            </div>
          )}

          {data && data.stories.length > 0 && (
            <div style={s.storyGrid}>
              {data.stories.map((story) => (
                <StoryCard key={story.ticker} story={story} mover={moversByTicker[story.ticker]} />
              ))}
            </div>
          )}
        </section>

        {data && (
          <section style={{ marginTop: "2.5rem" }}>
            <h2 style={s.sectionTitle}>Tracked Movers</h2>
            <div style={s.tableWrap}>
              <table style={s.table}>
                <thead>
                  <tr>
                    <th style={s.th}>Ticker</th>
                    <th style={s.th}>Close</th>
                    <th style={s.th}>Change</th>
                    <th style={s.th}>Volume</th>
                    <th style={s.th}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.classified_movers.map((m) => (
                    <MoverRow key={m.ticker} mover={m} />
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </main>

      <footer style={s.footer}>
        Built with LangGraph · RAG · guardrails · semantic caching &nbsp;·&nbsp; not investment advice
      </footer>
    </div>
  );
}

const s = {
  page: {
    minHeight: "100vh",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    color: "#14171f",
  },
  header: {
    borderBottom: "1px solid #e5e7eb",
    background: "#ffffff",
  },
  headerInner: {
    maxWidth: 880,
    margin: "0 auto",
    padding: "2rem 1.5rem",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    flexWrap: "wrap",
    gap: "0.75rem",
  },
  title: {
    margin: 0,
    fontSize: "1.75rem",
    fontWeight: 800,
    letterSpacing: "-0.02em",
  },
  subtitle: {
    margin: "0.35rem 0 0",
    color: "#6b7280",
    fontSize: "0.95rem",
  },
  dateBadge: {
    fontSize: "0.85rem",
    color: "#6b7280",
    background: "#f7f8fa",
    border: "1px solid #e5e7eb",
    borderRadius: 999,
    padding: "0.4rem 0.85rem",
  },
  main: {
    maxWidth: 880,
    margin: "0 auto",
    padding: "2.5rem 1.5rem 4rem",
  },
  sectionTitle: {
    fontSize: "1.1rem",
    fontWeight: 700,
    marginBottom: "1rem",
  },
  storyGrid: {
    display: "grid",
    gap: "1rem",
  },
  storyCard: {
    background: "#ffffff",
    border: "1px solid #e5e7eb",
    borderRadius: 12,
    padding: "1.25rem 1.5rem",
    boxShadow: "0 1px 2px rgba(16, 24, 40, 0.04)",
  },
  storyCardHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "0.6rem",
  },
  ticker: {
    margin: 0,
    fontSize: "1.05rem",
    fontWeight: 700,
  },
  storyText: {
    margin: 0,
    lineHeight: 1.6,
    color: "#26292f",
  },
  storyFooter: {
    marginTop: "0.85rem",
    fontSize: "0.75rem",
    color: "#9ca3af",
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  card: {
    background: "#ffffff",
    border: "1px solid #e5e7eb",
    borderRadius: 12,
    padding: "1.25rem 1.5rem",
    marginBottom: "1rem",
  },
  skeletonLine: {
    height: 12,
    borderRadius: 6,
    background: "linear-gradient(90deg, #f0f1f3 25%, #e5e7eb 37%, #f0f1f3 63%)",
    backgroundSize: "400% 100%",
    animation: "none",
    marginBottom: "0.6rem",
  },
  emptyState: {
    background: "#ffffff",
    border: "1px dashed #d1d5db",
    borderRadius: 12,
    padding: "2rem",
    textAlign: "center",
  },
  emptyIcon: {
    fontSize: "1.75rem",
    marginBottom: "0.5rem",
  },
  errorBox: {
    background: "#fef2f2",
    border: "1px solid #fecaca",
    color: "#991b1b",
    borderRadius: 12,
    padding: "1rem 1.25rem",
  },
  tableWrap: {
    background: "#ffffff",
    border: "1px solid #e5e7eb",
    borderRadius: 12,
    overflow: "hidden",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "0.9rem",
  },
  th: {
    textAlign: "left",
    padding: "0.75rem 1rem",
    background: "#f7f8fa",
    color: "#6b7280",
    fontWeight: 600,
    fontSize: "0.78rem",
    textTransform: "uppercase",
    letterSpacing: "0.03em",
    borderBottom: "1px solid #e5e7eb",
  },
  td: {
    padding: "0.7rem 1rem",
    borderBottom: "1px solid #f0f1f3",
  },
  badge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "0.25rem",
    fontSize: "0.85rem",
    fontWeight: 700,
    padding: "0.15rem 0.55rem",
    borderRadius: 999,
  },
  badgeUp: {
    color: "#16a34a",
    background: "#ecfdf3",
  },
  badgeDown: {
    color: "#dc2626",
    background: "#fef2f2",
  },
  pill: {
    fontSize: "0.75rem",
    fontWeight: 600,
    padding: "0.2rem 0.6rem",
    borderRadius: 999,
  },
  pillYes: {
    color: "#4f46e5",
    background: "#eef2ff",
  },
  pillNo: {
    color: "#6b7280",
    background: "#f3f4f6",
  },
  footer: {
    textAlign: "center",
    padding: "2rem 1.5rem",
    color: "#9ca3af",
    fontSize: "0.8rem",
  },
};
