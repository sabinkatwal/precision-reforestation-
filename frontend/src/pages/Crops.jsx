import { useEffect, useState } from "react";
import PageShell from "../components/PageShell.jsx";
import { getCropRecommendations } from "../services/api.js";
import { getStoredLocation } from "../services/location.js";

const SEASON_COLORS = {
  Kharif: "text-green-400 bg-green-400/10 border-green-400/20",
  Rabi: "text-blue-400 bg-blue-400/10 border-blue-400/20",
  "Year-round": "text-purple-400 bg-purple-400/10 border-purple-400/20",
};

const WATER_ICONS = { Low: "💧", Medium: "💧💧", High: "💧💧💧" };

export default function Crops() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const location = getStoredLocation();

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const res = await getCropRecommendations(location.lat, location.lng);
        if (mounted) setData(res.data);
      } catch (err) {
        if (mounted) setError(err?.response?.data?.detail || err.message);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    load();
    return () => { mounted = false; };
  }, [location.lat, location.lng]);

  return (
    <PageShell
      title="Crop Recommendations"
      subtitle="AI-powered crop suitability analysis based on real soil, elevation, and climate data."
      loading={loading}
      error={error}
      action={
        <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
          {data?.crops?.length ?? 0} crops found
        </div>
      }
    >
      {data && (
        <div className="space-y-5">

          {/* Summary bar */}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {[
              { label: "Best Season", value: data.best_season },
              { label: "Annual Rainfall", value: `${data.climate.annual_rainfall.toFixed(0)}mm` },
              { label: "Avg Temperature", value: `${data.climate.avg_temp_min}°–${data.climate.avg_temp_max}°C` },
              { label: "Irrigation", value: data.irrigation_needed ? "Required" : "Not Required" },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-[20px] border border-white/8 bg-black/20 p-4">
                <div className="text-xs uppercase tracking-widest text-slate-500">{label}</div>
                <div className="mt-2 font-semibold text-white">{value}</div>
              </div>
            ))}
          </div>

          {/* AI Insight */}
          <div className="rounded-[24px] border border-green-400/20 bg-green-400/5 p-5">
            <div className="text-xs uppercase tracking-widest text-green-400 mb-2">AI Insight</div>
            <p className="text-slate-200 leading-7">{data.insight}</p>
          </div>

          {/* Crop cards */}
          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
            {data.crops.map((crop, i) => (
              <div key={crop.name} className="rounded-[24px] border border-white/8 bg-black/20 p-5 space-y-4">

                {/* Header */}
                <div className="flex items-start justify-between">
                  <div>
                    <div className="text-xl font-bold text-white">{crop.name}</div>
                    <div className="text-sm text-slate-400 italic">{crop.local_name}</div>
                  </div>
                  <div className="text-2xl font-bold text-green-400">{crop.confidence}%</div>
                </div>

                {/* Season badge */}
                <span className={`inline-block text-xs font-mono px-3 py-1 rounded-full border ${SEASON_COLORS[crop.season]}`}>
                  {crop.season}
                </span>

                {/* Details grid */}
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="rounded-xl bg-white/5 p-3">
                    <div className="text-xs text-slate-500">Plant</div>
                    <div className="text-white font-medium">{crop.planting_month}</div>
                  </div>
                  <div className="rounded-xl bg-white/5 p-3">
                    <div className="text-xs text-slate-500">Harvest</div>
                    <div className="text-white font-medium">{crop.harvest_month}</div>
                  </div>
                  <div className="rounded-xl bg-white/5 p-3">
                    <div className="text-xs text-slate-500">Water</div>
                    <div className="text-white font-medium">{WATER_ICONS[crop.water_requirement]} {crop.water_requirement}</div>
                  </div>
                  <div className="rounded-xl bg-white/5 p-3">
                    <div className="text-xs text-slate-500">Yield</div>
                    <div className="text-white font-medium">{crop.yield_estimate}</div>
                  </div>
                </div>

                {/* Reason */}
                <p className="text-sm leading-6 text-slate-300">{crop.reason}</p>

                {/* Warnings */}
                {crop.warnings.length > 0 && (
                  <div className="space-y-1">
                    {crop.warnings.map((w) => (
                      <div key={w} className="flex items-start gap-2 text-xs text-yellow-400">
                        <span>⚠️</span><span>{w}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Soil context */}
          <div className="rounded-[24px] border border-white/8 bg-white/5 p-5">
            <div className="font-semibold text-white mb-4">Soil Context</div>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                { label: "pH", value: data.soil.ph.toFixed(2) },
                { label: "Nitrogen", value: `${data.soil.nitrogen.toFixed(3)} g/kg` },
                { label: "Clay", value: `${data.soil.clay.toFixed(1)}%` },
                { label: "Organic Matter", value: `${data.soil.organic_matter.toFixed(2)}%` },
              ].map(({ label, value }) => (
                <div key={label} className="rounded-2xl bg-black/20 p-4">
                  <div className="text-xs text-slate-400">{label}</div>
                  <div className="mt-1 text-lg font-semibold text-white">{value}</div>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}
    </PageShell>
  );
}