import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import MapView from "../components/MapView.jsx";
import SidePanel from "../components/SidePanel.jsx";
import { analyzePatch, getEnvironment } from "../services/api.js";
import { getStoredLocation, saveStoredAnalysis, saveStoredLocation } from "../services/location.js";
import { useTheme } from "../context/ThemeContext.jsx";

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

export default function Dashboard() {
  const { theme, toggleTheme } = useTheme();
  const [location, setLocation] = useState(() => getStoredLocation());
  const [latInput, setLatInput] = useState(() => String(getStoredLocation().lat));
  const [lngInput, setLngInput] = useState(() => String(getStoredLocation().lng));
  const [environment, setEnvironment] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState("Fetching soil data...");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    setLatInput(String(location.lat));
    setLngInput(String(location.lng));
  }, [location.lat, location.lng]);

  const runAnalysis = useCallback(async (nextLocation = location) => {
    const loc = nextLocation || location;
    setLocation(loc);
    saveStoredLocation(loc);
    setLoading(true);
    setError("");
    try {
      setStage("Fetching soil data...");
      const envRes = await getEnvironment(loc.lat, loc.lng);
      setEnvironment(envRes.data);
      await delay(150);
      setStage("Analyzing terrain...");
      await delay(150);
      setStage("Generating AI insights...");
      const anaRes = await analyzePatch(loc.lat, loc.lng);
      setAnalysis(anaRes.data);
      saveStoredAnalysis(anaRes.data);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Unable to analyze the selected area.");
    } finally {
      setLoading(false);
    }
  }, [location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const lat = parseFloat(latInput);
    const lng = parseFloat(lngInput);
    if (!isFinite(lat) || !isFinite(lng)) { setError("Enter valid lat/lng values."); return; }
    if (lat < -90 || lat > 90 || lng < -180 || lng > 180) { setError("Coordinates out of range."); return; }
    await runAnalysis({ lat, lng });
  };

  useEffect(() => { runAnalysis(location); }, []); // eslint-disable-line

  const handleExport = () => {
    const blob = new Blob([JSON.stringify({ location, environment, analysis, exportedAt: new Date().toISOString() }, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `restoration-${location.lat.toFixed(3)}-${location.lng.toFixed(3)}.json`;
    a.click(); URL.revokeObjectURL(url);
  };

  return (
    <>
      <style>{`
        .dash-root { font-family: 'DM Sans', sans-serif; min-height: 100vh; background: ${theme === "dark" ? "#020617" : "#f0fdf4"}; color: ${theme === "dark" ? "#e2e8f0" : "#052e16"}; }
        .dash-header {
          background: ${theme === "dark" ? "rgba(15,23,42,0.92)" : "rgba(255,255,255,0.92)"}; border: 1px solid ${theme === "dark" ? "rgba(148,163,184,0.14)" : "#dcfce7"};
          border-radius: 24px;
          padding: 20px 28px;
          display: flex; flex-direction: column; gap: 16px;
          box-shadow: 0 24px 80px ${theme === "dark" ? "rgba(0,0,0,0.32)" : "rgba(22,163,74,0.10)"};
          overflow: hidden;
        }
        .dash-title-row { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
        .dash-right-actions { display: flex; align-items: center; justify-content: flex-end; gap: 12px; }
        .dash-home-btn {
          background: ${theme === "dark" ? "rgba(255,255,255,0.05)" : "white"};
          color: ${theme === "dark" ? "#e2e8f0" : "#166534"};
          border: 1px solid ${theme === "dark" ? "rgba(148,163,184,0.2)" : "#16a34a"};
          border-radius: 999px;
          padding: 10px 18px;
          font-size: 0.9rem;
          font-weight: 700;
          cursor: pointer;
          transition: background 0.2s ease, color 0.2s ease, transform 0.15s ease;
        }
        .dash-home-btn:hover { background: ${theme === "dark" ? "rgba(255,255,255,0.1)" : "#16a34a"}; color: ${theme === "dark" ? "#fff" : "white"}; transform: translateY(-1px); }
        .dash-badge {
          display: inline-flex; align-items: center; gap: 6px;
          background: ${theme === "dark" ? "rgba(45,212,191,0.08)" : "#dcfce7"}; border: 1px solid ${theme === "dark" ? "rgba(45,212,191,0.18)" : "#86efac"};
          border-radius: 100px; padding: 4px 12px;
          font-size: 0.7rem; font-weight: 700; color: ${theme === "dark" ? "#5eead4" : "#15803d"};
          letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 8px;
        }
        .dash-badge-dot { width: 5px; height: 5px; border-radius: 50%; background: ${theme === "dark" ? "#2dd4bf" : "#22c55e"}; animation: pulse2 2s infinite; }
        .dash-logo-btn {
          display: flex; align-items: center; justify-content: center; gap: 10px;
          background: none; border: none; cursor: pointer;
          padding: 6px; margin-right: 16px;
          border-radius: 18px;
          transition: opacity 0.2s, transform 0.2s, box-shadow 0.2s;
        }
        .dash-logo-btn:hover { opacity: 0.9; transform: scale(1.02); box-shadow: 0 0 0 1px ${theme === "dark" ? "rgba(45,212,191,0.16)" : "rgba(22,163,74,0.16)"}, 0 0 24px ${theme === "dark" ? "rgba(45,212,191,0.12)" : "rgba(22,163,74,0.12)"}; }
        .dash-logo-img {
          height: 40px; width: 40px; object-fit: contain;
          filter: brightness(${theme === "dark" ? "1.1" : "0.85"}) drop-shadow(0 0 4px rgba(45, 212, 191, 0.2));
        }
        .dash-title {
          font-family: 'Playfair Display', serif;
          font-size: clamp(1.4rem, 3vw, 2rem); font-weight: 700; color: ${theme === "dark" ? "#e2e8f0" : "#052e16"};
        }
        .dash-subtitle { font-size: 0.875rem; color: ${theme === "dark" ? "#94a3b8" : "#4b7a59"}; margin-top: 4px; }
        .coord-badge {
          background: ${theme === "dark" ? "rgba(15,23,42,0.72)" : "#f0fdf4"}; border: 1px solid ${theme === "dark" ? "rgba(148,163,184,0.14)" : "#bbf7d0"};
          border-radius: 18px; padding: 12px 16px; text-align: right; flex-shrink: 0;
        }
        .coord-badge-label { display: block;
    font-size: 0.7rem;
    font-weight: 700;
    color: ${theme === "dark" ? "#5eead4" : "#16a34a"};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px; }
        .coord-badge-value { font-size: 1rem; font-weight: 600; color: ${theme === "dark" ? "#e2e8f0" : "#052e16"}; margin-top: 2px; }
        .dash-form {
          display: grid; gap: 12px;
          grid-template-columns: 1fr 1fr auto;
          background: ${theme === "dark" ? "rgba(15,23,42,0.72)" : "#f0fdf4"}; border: 1px solid ${theme === "dark" ? "rgba(148,163,184,0.14)" : "#bbf7d0"};
          border-radius: 18px; padding: 16px; overflow: hidden;
        }
        .form-field label { display: block; font-size: 0.7rem; font-weight: 700; color: ${theme === "dark" ? "#5eead4" : "#16a34a"}; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px; }
        .form-input {
          width: 100%; background: ${theme === "dark" ? "rgba(2,6,23,0.75)" : "white"}; border: 1px solid ${theme === "dark" ? "rgba(148,163,184,0.16)" : "#dcfce7"};
          border-radius: 14px; padding: 10px 14px; font-size: 0.9rem; color: ${theme === "dark" ? "#e2e8f0" : "#052e16"};
          outline: none; transition: border-color 0.2s;
          font-family: 'DM Sans', sans-serif;
        }
        .form-input:focus { border-color: ${theme === "dark" ? "#2dd4bf" : "#16a34a"}; }
        .form-submit {
          align-self: end;
          background: ${theme === "dark" ? "#2dd4bf" : "#16a34a"}; color: ${theme === "dark" ? "#052e16" : "white"}; border: none;
          border-radius: 14px; padding: 11px 24px;
          font-size: 0.875rem; font-weight: 600;
          cursor: pointer; transition: background 0.2s, transform 0.15s;
          white-space: nowrap; font-family: 'DM Sans', sans-serif;
        }
        .form-submit:hover { background: ${theme === "dark" ? "#5eead4" : "#15803d"}; transform: translateY(-1px); }
        .dash-error {
          background: ${theme === "dark" ? "rgba(127,29,29,0.18)" : "#fef2f2"}; border: 1px solid ${theme === "dark" ? "rgba(248,113,113,0.32)" : "#fecaca"};
          border-radius: 12px; padding: 12px 16px;
          font-size: 0.875rem; color: ${theme === "dark" ? "#fca5a5" : "#dc2626"};
        }
        .dash-body {
          display: grid; gap: 20px; padding: 20px 32px;
          grid-template-columns: minmax(0, 1.7fr) minmax(340px, 0.9fr);
        }
        @keyframes pulse2 { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.5;transform:scale(1.4)} }
        @media (max-width: 900px) {
          .dash-body { grid-template-columns: 1fr; padding: 16px; }
          .dash-header { padding: 16px; }
          .dash-form { grid-template-columns: 1fr 1fr; }
          .form-submit { grid-column: span 2; }
          .dash-right-actions { justify-content: flex-start; }
        }
        @media (max-width: 600px) {
          .dash-form { grid-template-columns: 1fr; }
          .form-submit { grid-column: 1; }
        }
      `}</style>

      <div className="dash-root">
        <div className="dash-header">
          <div className="dash-title-row">
            <div style={{ display: "flex", alignItems: "flex-start", gap: "0" }}>
              <button className="dash-logo-btn" onClick={() => navigate("/")} aria-label="Go to home">
                <img src="/logo.png" alt="Precision Reforestation" className="dash-logo-img" />
              </button>
              <div>
                <div className="dash-badge"><div className="dash-badge-dot" /> Live Analysis</div>
                <h1 className="dash-title">Restoration Intelligence Dashboard</h1>
                <p className="dash-subtitle">Click the map or enter coordinates to analyze any Nepal site.</p>
              </div>
            </div>
            <div className="dash-right-actions">
                <button className="dash-home-btn" type="button" onClick={toggleTheme}>
                  {theme === "dark" ? "☀ Light" : "☾ Dark"}
                </button>
                <button className="dash-home-btn" type="button" onClick={() => navigate("/")}>Home</button>
              <div className="coord-badge">
                <div className="coord-badge-label">Selected Point</div>
                <div className="coord-badge-value">{location.lat.toFixed(4)}, {location.lng.toFixed(4)}</div>
              </div>
            </div>
          </div>

          <form className="dash-form" onSubmit={handleSubmit}>
            <div className="form-field">
              <label>Latitude</label>
              <input className="form-input" type="number" step="any" value={latInput} onChange={(e) => setLatInput(e.target.value)} placeholder="27.7172" />
            </div>
            <div className="form-field">
              <label>Longitude</label>
              <input className="form-input" type="number" step="any" value={lngInput} onChange={(e) => setLngInput(e.target.value)} placeholder="85.3240" />
            </div>
            <button className="form-submit" type="submit">Analyze →</button>
          </form>

          {error && <div className="dash-error">⚠ {error}</div>}
        </div>

        <div className="dash-body">
          <MapView location={location} onSelect={runAnalysis} />
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
      </div>
    </>
  );
}
