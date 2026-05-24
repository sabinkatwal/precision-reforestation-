import { useEffect, useState } from "react";
import PageShell from "../components/PageShell.jsx";
import { analyzePatch } from "../services/api.js";
import { getStoredLocation } from "../services/location.js";

const cardStyles = `
  .gcard { background: white; border: 1px solid #dcfce7; border-radius: 24px; padding: 24px; transition: box-shadow 0.2s, border-color 0.2s; }
  .gcard:hover { border-color: #86efac; box-shadow: 0 4px 24px rgba(22,163,74,0.08); }
  .gcard-label { font-size: 0.7rem; font-weight: 700; color: #16a34a; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; }
  .gcard-text { font-size: 0.875rem; color: #4b7a59; line-height: 1.7; }
  .confidence-track { height: 6px; background: #dcfce7; border-radius: 100px; margin-top: 12px; overflow: hidden; }
  .confidence-fill { height: 100%; background: linear-gradient(90deg, #16a34a, #4ade80); border-radius: 100px; transition: width 0.8s ease; }
`;

export default function Species() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const location = getStoredLocation();

  useEffect(() => {
    let mounted = true;
    analyzePatch(location.lat, location.lng)
      .then((r) => { if (mounted) setAnalysis(r.data); })
      .catch((e) => { if (mounted) setError(e?.response?.data?.detail || e.message); })
      .finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, [location.lat, location.lng]);

  return (
    <PageShell
      title="Species Recommendations"
      subtitle="Native and climate-fit species suggestions from the AI layer."
      loading={loading} error={error}
      action={
        <span style={{ background: "#dcfce7", color: "#15803d", border: "1px solid #86efac", borderRadius: 100, padding: "6px 14px", fontSize: "0.8rem", fontWeight: 600 }}>
          {analysis?.species?.length ?? 0} suggestions
        </span>
      }
    >
      <style>{cardStyles}</style>
      <div style={{ display: "grid", gap: "16px", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))" }}>
        {analysis?.species?.length ? analysis.species.map((s) => (
          <div className="gcard" key={s.name}>
            <div className="gcard-label">Restoration Candidate</div>
            <div style={{ fontSize: "1.4rem", fontWeight: 700, color: "#052e16", marginBottom: 8 }}>{s.name}</div>
            <div className="gcard-text">{s.reason}</div>
            <div className="confidence-track">
              <div className="confidence-fill" style={{ width: `${s.confidence}%` }} />
            </div>
            <div style={{ fontSize: "0.75rem", color: "#16a34a", marginTop: 6, fontWeight: 600 }}>{s.confidence}% confidence</div>
          </div>
        )) : (
          <div className="gcard"><div className="gcard-text">No species data yet.</div></div>
        )}
      </div>
    </PageShell>
  );
}
