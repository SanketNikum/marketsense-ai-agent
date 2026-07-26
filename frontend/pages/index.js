import { useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

function PriceChange({ value, size = "normal" }) {
  const isUp = value >= 0;
  return (
    <span
      style={{
        ...s.badge,
        ...(isUp ? s.badgeUp : s.badgeDown),
        ...(size === "large" ? s.badgeLarge : {}),
      }}
    >
      {isUp ? "▲" : "▼"} {Math.abs(value).toFixed(2)}%
    </span>
  );
}

function LivePill() {
  const dateStr = new Date().toLocaleDateString("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
  return (
    <div style={s.livePill}>
      <span style={s.liveDot} />
      Live · {dateStr}
    </div>
  );
}

function StatTile({ label, value, accent }) {
  return (
    <div style={s.statTile}>
      <div style={{ ...s.statValue, color: accent || "var(--text)" }}>{value}</div>
      <div style={s.statLabel}>{label}</div>
    </div>
  );
}

function TopMoversChart({ movers }) {
  const top = useMemo(
    () =>
      [...movers]
        .sort((a, b) => Math.abs(b.pct_change) - Math.abs(a.pct_change))
        .slice(0, 8),
    [movers]
  );
  const max = Math.max(...top.map((m) => Math.abs(m.pct_change)), 1);

  return (
    <div style={s.chartCard}>
      {top.map((m) => {
        const isUp = m.pct_change >= 0;
        const widthPct = (Math.abs(m.pct_change) / max) * 100;
        return (
          <div key={m.ticker} style={s.chartRow}>
            <div style={s.chartLabel}>{m.ticker.replace(".NS", "")}</div>
            <div style={s.chartTrack}>
              <div
                style={{
                  ...s.chartBar,
                  width: `${widthPct}%`,
                  background: isUp ? "var(--up)" : "var(--down)",
                }}
              />
            </div>
            <div style={{ ...s.chartValue, color: isUp ? "var(--up)" : "var(--down)" }}>
              {isUp ? "+" : ""}
              {m.pct_change.toFixed(2)}%
            </div>
          </div>
        );
      })}
    </div>
  );
}

function StoryCard({ story, mover }) {
  return (
    <article style={s.storyCard} className="story-card">
      <div style={s.storyCardHeader}>
        <h3 style={s.ticker}>{story.ticker}</h3>
        {mover && <PriceChange value={mover.pct_change} />}
      </div>
      <p style={s.storyText}>{story.story}</p>
      <div style={s.storyFooter}>AI-generated · grounded in retrieved context</div>
    </article>
  );
}

function MoverRow({ mover, expanded, onToggle }) {
  return (
    <>
      <tr style={s.trClickable} onClick={onToggle}>
        <td style={s.td}>
          <span style={s.expandArrow}>{expanded ? "▾" : "▸"}</span>
          <strong>{mover.ticker}</strong>
        </td>
        <td style={s.td}>₹{mover.close.toLocaleString("en-IN")}</td>
        <td style={s.td}>
          <PriceChange value={mover.pct_change} />
        </td>
        <td style={{ ...s.td, color: "var(--text-muted)" }}>{mover.volume.toLocaleString("en-IN")}</td>
        <td style={s.td}>
          {mover.worth_story ? (
            <span style={{ ...s.pill, ...s.pillYes }}>story written</span>
          ) : (
            <span style={{ ...s.pill, ...s.pillNo }}>below threshold</span>
          )}
        </td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={5} style={s.reasonCell}>
            <span style={s.reasonLabel}>Classifier reasoning:</span> {mover.reason}
          </td>
        </tr>
      )}
    </>
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

const FILTERS = [
  { key: "all", label: "All" },
  { key: "story", label: "Story written" },
  { key: "below", label: "Below threshold" },
];

export default function Home() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [sortKey, setSortKey] = useState("pct_change");
  const [sortDir, setSortDir] = useState("desc");
  const [expandedTicker, setExpandedTicker] = useState(null);

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

  const visibleMovers = useMemo(() => {
    if (!data) return [];

    let rows = data.classified_movers;

    if (filter === "story") rows = rows.filter((m) => m.worth_story);
    if (filter === "below") rows = rows.filter((m) => !m.worth_story);
    if (search.trim()) {
      const q = search.trim().toUpperCase();
      rows = rows.filter((m) => m.ticker.toUpperCase().includes(q));
    }

    const sorted = [...rows].sort((a, b) => {
      let diff;
      if (sortKey === "ticker") diff = a.ticker.localeCompare(b.ticker);
      else diff = a[sortKey] - b[sortKey];
      return sortDir === "asc" ? diff : -diff;
    });

    return sorted;
  }, [data, filter, search, sortKey, sortDir]);

  function toggleSort(key) {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  function sortArrow(key) {
    if (sortKey !== key) return "";
    return sortDir === "asc" ? " ↑" : " ↓";
  }

  const storyCount = data ? data.classified_movers.filter((m) => m.worth_story).length : 0;
  const belowCount = data ? data.classified_movers.length - storyCount : 0;

  return (
    <div style={s.page}>
      <header style={s.header}>
        <div style={s.headerInner}>
          <div>
            <h1 style={s.title}>
              Market<span style={s.titleAccent}>Sense</span>
            </h1>
            <p style={s.subtitle}>AI-generated daily market explainers, grounded in real data</p>
          </div>
          <LivePill />
        </div>

        {data && (
          <div style={s.statsRow}>
            <StatTile label="Tracked stocks" value={data.classified_movers.length} />
            <StatTile label="Stories written" value={storyCount} accent="var(--up)" />
            <StatTile label="Below threshold" value={belowCount} accent="var(--text-muted)" />
          </div>
        )}
      </header>

      <main style={s.main}>
        {error && <div style={s.errorBox}>Couldn&apos;t reach the API: {error}</div>}

        {!data && !error && (
          <>
            <LoadingSkeleton />
            <LoadingSkeleton />
          </>
        )}

        {data && data.classified_movers.length > 0 && (
          <section style={{ marginBottom: "2.5rem" }}>
            <h2 style={s.sectionTitle}>Top Movers Today</h2>
            <TopMoversChart movers={data.classified_movers} />
          </section>
        )}

        {data && (
          <section>
            <h2 style={s.sectionTitle}>Today&apos;s Stories</h2>

            {data.stories.length === 0 && (
              <div style={s.emptyState}>
                <div style={s.emptyIcon}>📈</div>
                <p style={{ margin: 0, fontWeight: 600 }}>No significant moves worth a story today</p>
                <p style={{ margin: "0.25rem 0 0", color: "var(--text-muted)", fontSize: "0.9rem" }}>
                  The classifier reviews every tracked stock and only writes when a move clears its bar.
                </p>
              </div>
            )}

            {data.stories.length > 0 && (
              <div style={s.storyGrid}>
                {data.stories.map((story) => (
                  <StoryCard key={story.ticker} story={story} mover={moversByTicker[story.ticker]} />
                ))}
              </div>
            )}
          </section>
        )}

        {data && (
          <section style={{ marginTop: "2.5rem" }}>
            <h2 style={s.sectionTitle}>Tracked Movers</h2>

            <div style={s.toolbar}>
              <input
                style={s.searchInput}
                placeholder="Search ticker..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <div style={s.filterGroup}>
                {FILTERS.map((f) => (
                  <button
                    key={f.key}
                    onClick={() => setFilter(f.key)}
                    style={{
                      ...s.filterBtn,
                      ...(filter === f.key ? s.filterBtnActive : {}),
                    }}
                  >
                    {f.label}
                  </button>
                ))}
              </div>
            </div>

            <div style={s.tableWrap}>
              <table style={s.table}>
                <thead>
                  <tr>
                    <th style={s.th} onClick={() => toggleSort("ticker")}>
                      Ticker{sortArrow("ticker")}
                    </th>
                    <th style={s.th} onClick={() => toggleSort("close")}>
                      Close{sortArrow("close")}
                    </th>
                    <th style={s.th} onClick={() => toggleSort("pct_change")}>
                      Change{sortArrow("pct_change")}
                    </th>
                    <th style={s.th} onClick={() => toggleSort("volume")}>
                      Volume{sortArrow("volume")}
                    </th>
                    <th style={s.th}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleMovers.map((m) => (
                    <MoverRow
                      key={m.ticker}
                      mover={m}
                      expanded={expandedTicker === m.ticker}
                      onToggle={() => setExpandedTicker(expandedTicker === m.ticker ? null : m.ticker)}
                    />
                  ))}
                  {visibleMovers.length === 0 && (
                    <tr>
                      <td colSpan={5} style={{ ...s.td, textAlign: "center", color: "var(--text-muted)" }}>
                        No movers match this filter/search.
                      </td>
                    </tr>
                  )}
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
    color: "#e6e9f0",
  },
  header: {
    borderBottom: "1px solid #232a3b",
    background: "linear-gradient(180deg, #121722 0%, #0b0e14 100%)",
  },
  headerInner: {
    maxWidth: 960,
    margin: "0 auto",
    padding: "2.5rem 1.5rem 1.5rem",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    flexWrap: "wrap",
    gap: "0.75rem",
  },
  title: {
    margin: 0,
    fontSize: "2.25rem",
    fontWeight: 800,
    letterSpacing: "-0.03em",
  },
  titleAccent: {
    color: "#818cf8",
  },
  subtitle: {
    margin: "0.4rem 0 0",
    color: "#8b93a7",
    fontSize: "0.95rem",
  },
  livePill: {
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    fontSize: "0.85rem",
    color: "#8b93a7",
    background: "#171d2b",
    border: "1px solid #232a3b",
    borderRadius: 999,
    padding: "0.45rem 0.9rem",
  },
  liveDot: {
    width: 8,
    height: 8,
    borderRadius: "50%",
    background: "#22c55e",
    display: "inline-block",
    animation: "pulse 1.8s ease-in-out infinite",
  },
  statsRow: {
    maxWidth: 960,
    margin: "0 auto",
    padding: "0 1.5rem 2rem",
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
    gap: "1rem",
  },
  statTile: {
    background: "#121722",
    border: "1px solid #232a3b",
    borderRadius: 14,
    padding: "1rem 1.25rem",
  },
  statValue: {
    fontSize: "1.6rem",
    fontWeight: 800,
  },
  statLabel: {
    fontSize: "0.8rem",
    color: "#8b93a7",
    marginTop: "0.15rem",
  },
  main: {
    maxWidth: 960,
    margin: "0 auto",
    padding: "2.5rem 1.5rem 4rem",
  },
  sectionTitle: {
    fontSize: "1.1rem",
    fontWeight: 700,
    marginBottom: "1rem",
  },
  chartCard: {
    background: "#121722",
    border: "1px solid #232a3b",
    borderRadius: 14,
    padding: "1.25rem 1.5rem",
  },
  chartRow: {
    display: "grid",
    gridTemplateColumns: "110px 1fr 70px",
    alignItems: "center",
    gap: "0.75rem",
    padding: "0.4rem 0",
  },
  chartLabel: {
    fontSize: "0.85rem",
    fontWeight: 600,
    color: "#e6e9f0",
  },
  chartTrack: {
    background: "#0b0e14",
    borderRadius: 6,
    height: 10,
    overflow: "hidden",
  },
  chartBar: {
    height: "100%",
    borderRadius: 6,
    transition: "width 0.3s ease",
  },
  chartValue: {
    fontSize: "0.82rem",
    fontWeight: 700,
    textAlign: "right",
  },
  storyGrid: {
    display: "grid",
    gap: "1rem",
  },
  storyCard: {
    background: "#121722",
    border: "1px solid #232a3b",
    borderRadius: 14,
    padding: "1.25rem 1.5rem",
    transition: "transform 0.15s ease, border-color 0.15s ease",
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
    color: "#c3c8d4",
  },
  storyFooter: {
    marginTop: "0.85rem",
    fontSize: "0.72rem",
    color: "#5b6376",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  card: {
    background: "#121722",
    border: "1px solid #232a3b",
    borderRadius: 14,
    padding: "1.25rem 1.5rem",
    marginBottom: "1rem",
  },
  skeletonLine: {
    height: 12,
    borderRadius: 6,
    background: "#1a2030",
    marginBottom: "0.6rem",
  },
  emptyState: {
    background: "#121722",
    border: "1px dashed #2c3346",
    borderRadius: 14,
    padding: "2rem",
    textAlign: "center",
  },
  emptyIcon: {
    fontSize: "1.75rem",
    marginBottom: "0.5rem",
  },
  errorBox: {
    background: "rgba(239, 68, 68, 0.1)",
    border: "1px solid rgba(239, 68, 68, 0.35)",
    color: "#fca5a5",
    borderRadius: 14,
    padding: "1rem 1.25rem",
  },
  toolbar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "0.75rem",
    marginBottom: "1rem",
  },
  searchInput: {
    background: "#121722",
    border: "1px solid #232a3b",
    color: "#e6e9f0",
    borderRadius: 10,
    padding: "0.5rem 0.85rem",
    fontSize: "0.85rem",
    minWidth: 180,
    outline: "none",
  },
  filterGroup: {
    display: "flex",
    gap: "0.4rem",
  },
  filterBtn: {
    background: "#121722",
    border: "1px solid #232a3b",
    color: "#8b93a7",
    borderRadius: 999,
    padding: "0.4rem 0.85rem",
    fontSize: "0.8rem",
    cursor: "pointer",
  },
  filterBtnActive: {
    background: "rgba(129, 140, 248, 0.14)",
    borderColor: "#818cf8",
    color: "#818cf8",
  },
  tableWrap: {
    background: "#121722",
    border: "1px solid #232a3b",
    borderRadius: 14,
    overflow: "hidden",
  },
  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: "0.87rem",
  },
  th: {
    textAlign: "left",
    padding: "0.75rem 1rem",
    background: "#171d2b",
    color: "#8b93a7",
    fontWeight: 600,
    fontSize: "0.75rem",
    textTransform: "uppercase",
    letterSpacing: "0.04em",
    borderBottom: "1px solid #232a3b",
    cursor: "pointer",
    userSelect: "none",
  },
  trClickable: {
    cursor: "pointer",
  },
  td: {
    padding: "0.65rem 1rem",
    borderBottom: "1px solid #1a2030",
  },
  expandArrow: {
    display: "inline-block",
    width: "1rem",
    color: "#5b6376",
  },
  reasonCell: {
    padding: "0.75rem 1rem 0.9rem 2.5rem",
    background: "#0e1219",
    borderBottom: "1px solid #1a2030",
    color: "#a8afbd",
    fontSize: "0.85rem",
    lineHeight: 1.5,
  },
  reasonLabel: {
    color: "#818cf8",
    fontWeight: 600,
  },
  badge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "0.25rem",
    fontSize: "0.82rem",
    fontWeight: 700,
    padding: "0.15rem 0.55rem",
    borderRadius: 999,
  },
  badgeLarge: {
    fontSize: "1rem",
    padding: "0.3rem 0.75rem",
  },
  badgeUp: {
    color: "#22c55e",
    background: "rgba(34, 197, 94, 0.14)",
  },
  badgeDown: {
    color: "#ef4444",
    background: "rgba(239, 68, 68, 0.14)",
  },
  pill: {
    fontSize: "0.72rem",
    fontWeight: 600,
    padding: "0.2rem 0.6rem",
    borderRadius: 999,
  },
  pillYes: {
    color: "#818cf8",
    background: "rgba(129, 140, 248, 0.14)",
  },
  pillNo: {
    color: "#8b93a7",
    background: "rgba(139, 147, 167, 0.12)",
  },
  footer: {
    textAlign: "center",
    padding: "2rem 1.5rem",
    color: "#5b6376",
    fontSize: "0.8rem",
  },
};
