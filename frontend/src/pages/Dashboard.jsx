import { useEffect, useState } from "react";
import MapView from "../components/MapView.jsx";
import SidePanel from "../components/SidePanel.jsx";
import { analyzePatch, getEnvironment } from "../services/api.js";
import {
  getStoredLocation,
  saveStoredAnalysis,
  saveStoredLocation,
} from "../services/location.js";

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export default function Dashboard() {
  const [location, setLocation] = useState(() => getStoredLocation());
  const [latInput, setLatInput] = useState(() => String(getStoredLocation().lat));
  const [lngInput, setLngInput] = useState(() => String(getStoredLocation().lng));
  const [environment, setEnvironment] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState("Fetching soil data...");
  const [error, setError] = useState("");

  useEffect(() => {
    setLatInput(String(location.lat));
    setLngInput(String(location.lng));
  }, [location.lat, location.lng]);

  const runAnalysis = async (nextLocation = location) => {
    const resolvedLocation = nextLocation || location;
    setLocation(resolvedLocation);
    saveStoredLocation(resolvedLocation);
    setLoading(true);
    setError("");

    try {
      setStage("Fetching soil data...");
      const environmentResponse = await getEnvironment(resolvedLocation.lat, resolvedLocation.lng);
      setEnvironment(environmentResponse.data);

      await delay(180);
      setStage("Analyzing terrain...");

      await delay(180);
      setStage("Generating AI insights...");
      const analysisResponse = await analyzePatch(resolvedLocation.lat, resolvedLocation.lng);
      setAnalysis(analysisResponse.data);
      saveStoredAnalysis(analysisResponse.data);
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError.message || "Unable to analyze the selected area.");
    } finally {
      setLoading(false);
    }
  };

  const handleCoordinateSubmit = async (event) => {
    event.preventDefault();
    const nextLat = Number.parseFloat(latInput);
    const nextLng = Number.parseFloat(lngInput);

    if (!Number.isFinite(nextLat) || !Number.isFinite(nextLng)) {
      setError("Enter valid latitude and longitude values.");
      return;
    }

    if (nextLat < -90 || nextLat > 90 || nextLng < -180 || nextLng > 180) {
      setError("Latitude must be between -90 and 90, and longitude between -180 and 180.");
      return;
    }

    await runAnalysis({ lat: nextLat, lng: nextLng });
  };

  useEffect(() => {
    runAnalysis(location);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleExport = () => {
    const payload = {
      location,
      environment,
      analysis,
      exportedAt: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `nepal-restoration-report-${location.lat.toFixed(3)}-${location.lng.toFixed(3)}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="grid gap-5 xl:grid-cols-[minmax(0,1.7fr)_minmax(380px,0.9fr)]">
      <div className="space-y-5">
        <div className="glass-panel rounded-[28px] border border-white/10 p-5 md:p-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="inline-flex rounded-full border border-forest-400/20 bg-forest-400/10 px-3 py-1 text-xs uppercase tracking-[0.28em] text-forest-200">
                Kathmandu-first restoration demo
              </div>
              <h1 className="mt-4 font-display text-4xl font-bold text-white md:text-5xl">
                AI-Powered Ecological Restoration Intelligence Platform
              </h1>
              <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400 md:text-base">
                Enter latitude and longitude, or click any point in Nepal, to pull soil and elevation data, estimate terrain exposure, and ask Claude for restoration guidance.
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
              <div className="text-xs uppercase tracking-[0.24em] text-slate-500">Selected Coordinate</div>
              <div className="mt-1 font-semibold text-white">
                {location.lat.toFixed(5)}, {location.lng.toFixed(5)}
              </div>
            </div>
          </div>

          <form onSubmit={handleCoordinateSubmit} className="mt-5 grid gap-3 rounded-3xl border border-white/8 bg-black/15 p-4 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto] md:items-end">
            <label className="block">
              <span className="mb-2 block text-xs uppercase tracking-[0.24em] text-slate-500">Latitude</span>
              <input
                type="number"
                step="any"
                value={latInput}
                onChange={(event) => setLatInput(event.target.value)}
                className="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-forest-400/50"
                placeholder="27.7172"
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-xs uppercase tracking-[0.24em] text-slate-500">Longitude</span>
              <input
                type="number"
                step="any"
                value={lngInput}
                onChange={(event) => setLngInput(event.target.value)}
                className="w-full rounded-2xl border border-white/10 bg-slate-950/60 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-forest-400/50"
                placeholder="85.3240"
              />
            </label>
            <button
              type="submit"
              className="rounded-2xl bg-forest-500 px-5 py-3 text-sm font-semibold text-slate-950 transition hover:bg-forest-400"
            >
              Use Coordinates
            </button>
          </form>
        </div>

        <MapView location={location} onSelect={runAnalysis} />
      </div>

      <SidePanel
        location={location}
        environment={environment}
        analysis={analysis}
        loading={loading}
        stage={stage}
        error={error}
        onAnalyze={() => runAnalysis(location)}
        onExport={handleExport}
      />
    </div>
  );
}
