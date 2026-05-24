import { useEffect, useState } from "react";
import PageShell from "../components/PageShell.jsx";
import ConfidenceBar from "../components/ConfidenceBar.jsx";
import { analyzePatch } from "../services/api.js";
import { getStoredLocation } from "../services/location.js";

export default function Biodiversity() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const location = getStoredLocation();

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        const response = await analyzePatch(location.lat, location.lng);
        if (mounted) {
          setAnalysis(response.data);
        }
      } catch (requestError) {
        if (mounted) {
          setError(requestError?.response?.data?.detail || requestError.message || "Unable to fetch biodiversity analysis.");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    load();
    return () => {
      mounted = false;
    };
  }, [location.lat, location.lng]);

  const score = analysis?.biodiversity_score ?? 0;
  const summary = score >= 75 ? "High ecological recovery potential" : score >= 50 ? "Moderate biodiversity opportunity" : "Targeted restoration needed";

  return (
    <PageShell
      title="Biodiversity"
      subtitle="Understand how the selected Nepal site scores for species richness and ecological resilience."
      loading={loading}
      error={error}
      action={
        <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
          <span className="text-slate-500">Location</span> {location.lat.toFixed(3)}, {location.lng.toFixed(3)}
        </div>
      }
    >
      <div className="grid gap-5 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-[24px] border border-white/8 bg-black/20 p-5">
          <div className="text-sm uppercase tracking-[0.24em] text-slate-500">Biodiversity Score</div>
          <div className="mt-3 font-display text-6xl font-bold text-white">{score.toFixed(1)}</div>
          <div className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">{summary}</div>
          <div className="mt-6">
            <ConfidenceBar value={score} />
          </div>
        </div>

        <div className="rounded-[24px] border border-white/8 bg-white/5 p-5">
          <div className="font-semibold text-white">Logic</div>
          <div className="mt-3 space-y-3 text-sm leading-6 text-slate-300">
            <p>The backend combines live soil and elevation context with generated NDVI and slope estimates, then scores the site through Claude. If an upstream API is unavailable, the request fails instead of fabricating data.</p>
            <p>Higher NDVI, stronger organic matter, and moderate slopes typically improve the score, while steep or nutrient-poor terrain pulls it down.</p>
          </div>
        </div>
      </div>
    </PageShell>
  );
}
