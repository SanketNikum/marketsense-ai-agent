import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/stories`)
      .then((res) => res.json())
      .then(setData)
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <main style={styles.main}><p>Error: {error}</p></main>;
  if (!data) return <main style={styles.main}><p>Loading today&apos;s market stories...</p></main>;

  return (
    <main style={styles.main}>
      <h1>MarketSense</h1>
      <p style={{ color: "#666" }}>AI-generated daily market explainers</p>

      {data.stories.length === 0 && (
        <p style={styles.card}>No significant moves worth a story today.</p>
      )}

      {data.stories.map((story) => (
        <div key={story.ticker} style={styles.card}>
          <h2>{story.ticker}</h2>
          <p>{story.story}</p>
        </div>
      ))}

      <h3 style={{ marginTop: "2rem" }}>All tracked movers today</h3>
      <ul>
        {data.classified_movers.map((m) => (
          <li key={m.ticker}>
            {m.ticker}: {m.pct_change}% (worth_story: {String(m.worth_story)})
          </li>
        ))}
      </ul>
    </main>
  );
}

const styles = {
  main: { maxWidth: 700, margin: "0 auto", padding: "2rem", fontFamily: "system-ui, sans-serif" },
  card: { border: "1px solid #ddd", borderRadius: 8, padding: "1rem", marginBottom: "1rem" },
};
