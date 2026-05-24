import { useEffect, useState } from "react";
import PageShell from "../components/PageShell.jsx";
import { analyzePatch } from "../services/api.js";
import { getStoredLocation } from "../services/location.js";

export default function Carbon() {
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

  const carbon = analysis?.carbon_potential ?? 0;

  return (
    <PageShell
      title="Carbon Potential"
      subtitle="Estimate restoration-linked carbon sequestration from terrain, soil, and vegetation."
      loading={loading} error={error}
      action={
        <span style={{ background: "#dcfce7", color: "#15803d", border: "1px solid #86efac", borderRadius: 100, padding: "6px 14px", fontSize: "0.8rem", fontWeight: 600 }}>
          CO₂e {carbon.toFixed(2)} t/yr
        </span>
      }
    >
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap');
        .carbon-grid { display: grid; gap: 16px; grid-template-columns: 1fr 1fr; }
        .ccard { background: white; border: 1px solid #dcfce7; border-radius: 24px; padding: 24px; }
        .ccard-label { font-size: 0.7rem; font-weight: 700; color: #16a34a; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; }
        .ccard-value { font-family: 'Playfair Display', serif; font-size: 3.5rem; font-weight: 700; color: #052e16; line-height: 1; }
        .ccard-unit { font-size: 0.875rem; color: #4b7a59; margin-top: 6px; }
        .ccard-title { font-size: 1rem; font-weight: 600; color: #052e16; margin-bottom: 14px; }
        .ccard-text { font-size: 0.875rem; color: #4b7a59; line-height: 1.7; }
        .cstat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; }
        .cstat { background: #f0fdf4; border-radius: 14px; padding: 14px; }
        .cstat-label { font-size: 0.65rem; color: #16a34a; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
        .cstat-value { font-size: 1.2rem; font-weight: 600; color: #052e16; margin-top: 4px; }
        @media (max-width: 768px) { .carbon-grid { grid-template-columns: 1fr; } }
      `}</style>
      <div className="carbon-grid">
        <div className="ccard">
          <div className="ccard-label">Carbon Potential</div>
          <div className="ccard-value">{carbon.toFixed(2)}</div>
          <div className="ccard-unit">tons of CO₂e per year</div>
          <p className="ccard-text" style={{ marginTop: 12 }}>Organic matter and canopy recovery increase the site's sequestration capacity.</p>
        </div>
        <div className="ccard">
          <div className="ccard-title">Key Drivers</div>
          <div className="cstat-grid">
            <div className="cstat">
              <div className="cstat-label">Organic Matter</div>
              <div className="cstat-value">{analysis?.environment?.soil?.organic_matter?.toFixed(2) ?? "—"}%</div>
            </div>
            <div className="cstat">
              <div className="cstat-label">NDVI</div>
              <div className="cstat-value">{analysis?.environment?.ndvi?.toFixed(3) ?? "—"}</div>
            </div>
          </div>
          <p className="ccard-text">Higher organic matter signals stronger biomass accumulation and better long-term carbon storage potential.</p>
        </div>
      </div>
    </PageShell>
  );
}
