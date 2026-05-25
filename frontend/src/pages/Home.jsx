import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTheme } from "../context/ThemeContext.jsx";

// Animated SVG tree
function Tree({ x, y, scale = 1, delay = 0, opacity = 1 }) {
  return (
    <g
      transform={`translate(${x}, ${y}) scale(${scale})`}
      style={{
        opacity: 0,
        ["--tree-opacity"]: opacity,
        animation: `treeAppear 0.8s ease-out ${delay}s forwards`,
        filter: "drop-shadow(0 0 8px rgba(34, 197, 94, 0.22)) drop-shadow(0 0 18px rgba(20, 184, 166, 0.12))",
      }}
    >
      <line x1="0" y1="0" x2="0" y2="60" stroke="#14532d" strokeWidth="4" strokeLinecap="round" />
      <polygon points="0,-55 -22,0 22,0" fill="#166534" opacity="0.98" />
      <polygon points="0,-75 -18,-20 18,-20" fill="#22c55e" opacity="0.92" />
      <polygon points="0,-90 -13,-40 13,-40" fill="#86efac" opacity="0.9" />
    </g>
  );
}

function ForestBackground() {
  const trees = [
    { x: 60, y: 350, scale: 0.72, delay: 0.2 },
    { x: 140, y: 370, scale: 0.94, delay: 0.5 },
    { x: 220, y: 340, scale: 0.64, delay: 0.8 },
    { x: 310, y: 380, scale: 1.12, delay: 0.3 },
    { x: 400, y: 350, scale: 0.84, delay: 0.7 },
    { x: 500, y: 375, scale: 1.0, delay: 0.1 },
    { x: 600, y: 345, scale: 0.8, delay: 0.9 },
    { x: 700, y: 370, scale: 1.22, delay: 0.4 },
    { x: 800, y: 350, scale: 0.9, delay: 0.6 },
    { x: 900, y: 380, scale: 0.98, delay: 0.2 },
    { x: 980, y: 340, scale: 0.74, delay: 0.8 },
    { x: 1060, y: 365, scale: 1.08, delay: 0.5 },
    { x: 1150, y: 350, scale: 0.84, delay: 0.3 },
    { x: 1240, y: 375, scale: 0.94, delay: 0.7 },
    { x: 1320, y: 345, scale: 1.12, delay: 0.1 },
    // back row (smaller)
    { x: 100, y: 300, scale: 0.5, delay: 0.4, opacity: 0.65 },
    { x: 260, y: 285, scale: 0.45, delay: 0.6, opacity: 0.65 },
    { x: 450, y: 295, scale: 0.55, delay: 0.2, opacity: 0.65 },
    { x: 650, y: 280, scale: 0.5, delay: 0.9, opacity: 0.65 },
    { x: 850, y: 290, scale: 0.48, delay: 0.5, opacity: 0.65 },
    { x: 1050, y: 300, scale: 0.52, delay: 0.3, opacity: 0.65 },
    { x: 1200, y: 285, scale: 0.46, delay: 0.7, opacity: 0.65 },
  ];

  return (
    <svg
      viewBox="0 0 1400 500"
      preserveAspectRatio="xMidYMax slice"
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{ zIndex: 0, overflow: "visible" }}
    >
      <defs>
        <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#f0fdf4" />
          <stop offset="70%" stopColor="#dcfce7" />
          <stop offset="100%" stopColor="#bbf7d0" />
        </linearGradient>
        <linearGradient id="groundGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#4ade80" />
          <stop offset="100%" stopColor="#16a34a" />
        </linearGradient>
      </defs>
      {/* Ground */}
      <rect x="0" y="430" width="1400" height="70" fill="url(#groundGrad)" rx="0" />
      <ellipse cx="700" cy="436" rx="760" ry="22" fill="#22c55e" opacity="0.5" />
      {/* Trees */}
      {trees.map((t, i) => (
        <Tree key={i} {...t} />
      ))}
      {/* Rolling hills */}
      <path d="M0,455 Q200,395 400,435 Q600,465 800,425 Q1000,395 1200,440 Q1300,455 1400,435 L1400,500 L0,500 Z" fill="#16a34a" opacity="0.42" />
    </svg>
  );
}

function StatCard({ value, label, icon }) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

export default function Home() {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();
  const [visible, setVisible] = useState(false);
  const [activeView, setActiveView] = useState("hero");
  const [spotlight, setSpotlight] = useState("map");

  const spotlightCards = {
    map: {
      label: "Site mapping",
      title: "Start with a point",
      text: "Click a location and the app instantly layers terrain, soil, and NDVI context for that patch.",
      stat: "1 tap",
    },
    species: {
      label: "Species fit",
      title: "Match native trees",
      text: "See which species rise to the top before you ever leave the homepage.",
      stat: "Live AI",
    },
    dashboard: {
      label: "Analysis workspace",
      title: "Open the full dashboard",
      text: "Move from overview to the full restoration workflow without losing the visual thread.",
      stat: "Ready",
    },
  };

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 100);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="home-root" data-theme={theme}>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }

        html,
        body {
          overflow: hidden;
        }

        .home-root {
          min-height: 100vh;
          background: var(--home-bg);
          font-family: 'DM Sans', sans-serif;
          overflow-x: hidden;
          overflow-y: auto;
          --home-bg: #f0fdf4;
          --home-nav-bg: rgba(240, 253, 244, 0.88);
          --home-border: #bbf7d0;
          --home-text: #052e16;
          --home-text-soft: #166534;
          --home-muted: #4b7a59;
          --home-surface: rgba(255, 255, 255, 0.94);
          --home-surface-alt: #dcfce7;
          --home-surface-strong: #ffffff;
          --home-surface-shadow: rgba(22, 163, 74, 0.12);
          --home-accent: #16a34a;
          --home-accent-strong: #15803d;
          --home-accent-soft: #86efac;
          --home-accent-glow: rgba(20, 184, 166, 0.24);
        }
        .home-root[data-theme='dark'] {
          --home-bg: #020617;
          --home-nav-bg: rgba(2, 6, 23, 0.82);
          --home-border: rgba(148, 163, 184, 0.14);
          --home-text: #e2e8f0;
          --home-text-soft: #cbd5e1;
          --home-muted: #94a3b8;
          --home-surface: rgba(15, 23, 42, 0.92);
          --home-surface-alt: rgba(15, 23, 42, 0.76);
          --home-surface-strong: #0f172a;
          --home-surface-shadow: rgba(0, 0, 0, 0.35);
          --home-accent: #2dd4bf;
          --home-accent-strong: #14b8a6;
          --home-accent-soft: #5eead4;
          --home-accent-glow: rgba(45, 212, 191, 0.28);
        }

        /* NAV */
        .home-nav {
          position: fixed; top: 0; left: 0; right: 0; z-index: 100;
          display: flex; align-items: center; justify-content: space-between;
          padding: 18px 40px;
          background: var(--home-nav-bg);
          backdrop-filter: blur(12px);
          border-bottom: 1px solid var(--home-border);
        }
        .nav-logo {
          display: flex; align-items: center; gap: 12px;
          font-family: 'Playfair Display', serif;
          font-size: 1.3rem; font-weight: 700; color: var(--home-text);
          cursor: pointer;
          transition: opacity 0.2s, transform 0.2s;
          background: none; border: none; padding: 0;
        }
        .nav-logo:hover { opacity: 0.8; transform: scale(1.02); }
        .nav-logo-image {
          height: 44px; width: 44px; display: block; align-self: center;
          object-fit: contain;
          border-radius: 8px;
          background: transparent;
          padding: 0;
          filter: brightness(var(--logo-brightness, 1)) drop-shadow(0 0 4px rgba(45, 212, 191, 0.2));
          transition: filter 0.2s, transform 0.12s;
        }
        .home-root[data-theme='light'] .nav-logo-image {
          --logo-brightness: 0.85;
        }
        .home-root[data-theme='dark'] .nav-logo-image {
          --logo-brightness: 1.1;
        }
        .nav-logo-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--home-accent); }
        .nav-links { display: flex; gap: 32px; }
        .nav-link {
          font-size: 0.875rem; font-weight: 500; color: var(--home-text-soft);
          text-decoration: none; letter-spacing: 0.02em;
          transition: color 0.2s;
        }
        .nav-link:hover { color: var(--home-accent); }
        .nav-actions { display: flex; align-items: center; gap: 12px; }
        .nav-theme-toggle {
          display: inline-flex; align-items: center; justify-content: center; gap: 8px;
          min-width: 120px;
          padding: 10px 16px;
          border-radius: 999px;
          border: 1px solid var(--home-border);
          background: var(--home-surface);
          color: var(--home-text);
          font-size: 0.82rem; font-weight: 700;
          cursor: pointer;
          transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }
        .nav-theme-toggle:hover {
          transform: translateY(-1px);
          border-color: var(--home-accent-soft);
          box-shadow: 0 14px 28px var(--home-surface-shadow);
        }
        .nav-cta {
          background: var(--home-accent); color: #052e16;
          border: none; border-radius: 100px;
          padding: 10px 24px; font-size: 0.875rem; font-weight: 600;
          cursor: pointer; transition: background 0.2s, transform 0.15s;
          font-family: 'DM Sans', sans-serif;
        }
        .nav-cta:hover { background: var(--home-accent-soft); transform: translateY(-1px); }

        /* HERO */
        .hero {
          position: relative; min-height: 100vh;
          display: flex; flex-direction: column; align-items: center; justify-content: center;
          padding: 120px 40px 70px;
          overflow: hidden;
        }
        .hero::before {
          content: '';
          position: absolute;
          inset: 0;
          background: radial-gradient(circle at top, var(--home-accent-glow) 0%, transparent 55%);
          pointer-events: none;
        }
        .hero::after {
          content: '';
          position: absolute;
          inset: 0;
          background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.02) 50%, transparent 100%);
          animation: heroDrift 10s ease-in-out infinite alternate;
          pointer-events: none;
        }
        .hero-stage {
          position: relative;
          z-index: 2;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          width: 100%;
        }
        .hero-content {
          position: relative; z-index: 10;
          text-align: center; max-width: 800px;
          opacity: 0; transform: translateX(42px);
          transition: opacity 0.8s ease, transform 0.8s ease;
        }
        .hero-content.visible { animation: contentSlideIn 0.9s cubic-bezier(0.16, 1, 0.3, 1) forwards 0.2s; }
        .hero-badge {
          display: inline-flex; align-items: center; gap: 8px;
          background: var(--home-surface-alt); border: 1px solid var(--home-accent-soft);
          border-radius: 100px; padding: 6px 16px;
          font-size: 0.75rem; font-weight: 600; color: var(--home-accent-strong);
          letter-spacing: 0.08em; text-transform: uppercase;
          margin-bottom: 24px;
        }
        .hero-badge-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--home-accent); animation: pulse 2s infinite; }
        .hero-title {
          font-family: 'Playfair Display', serif;
          font-size: clamp(2.8rem, 6vw, 5rem);
          font-weight: 900; line-height: 1.1;
          color: var(--home-text); margin-bottom: 20px;
        }
        .hero-title span { color: var(--home-accent); }
        .hero-subtitle {
          font-size: clamp(1rem, 2vw, 1.2rem);
          color: var(--home-text-soft); line-height: 1.7; max-width: 560px; margin: 0 auto 40px;
          font-weight: 300;
        }
        .hero-actions { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }
        .hero-spotlight {
          margin: 28px auto 0;
          max-width: 760px;
          border: 1px solid var(--home-border);
          border-radius: 28px;
          background: linear-gradient(180deg, var(--home-surface), var(--home-surface-strong));
          box-shadow: 0 20px 60px var(--home-surface-shadow);
          overflow: hidden;
          transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .hero-spotlight:hover {
          transform: translateY(-2px);
          box-shadow: 0 24px 72px var(--home-surface-shadow);
        }
        .hero-spotlight-tabs {
          display: flex;
          gap: 8px;
          padding: 12px;
          flex-wrap: wrap;
          border-bottom: 1px solid var(--home-border);
        }
        .spotlight-tab {
          border: 1px solid transparent;
          background: transparent;
          color: var(--home-text-soft);
          border-radius: 999px;
          padding: 10px 14px;
          font-size: 0.8rem;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.2s ease;
        }
        .spotlight-tab:hover {
          background: var(--home-surface-alt);
          color: var(--home-text);
        }
        .spotlight-tab.active {
          background: var(--home-accent);
          color: #052e16;
          box-shadow: 0 10px 24px var(--home-surface-shadow);
        }
        .hero-spotlight-body {
          display: grid;
          grid-template-columns: minmax(0, 1.4fr) minmax(180px, 0.6fr);
          gap: 16px;
          padding: 18px;
          text-align: left;
          align-items: center;
        }
        .hero-spotlight-label {
          font-size: 0.72rem;
          font-weight: 800;
          color: var(--home-accent-strong);
          text-transform: uppercase;
          letter-spacing: 0.1em;
          margin-bottom: 8px;
        }
        .hero-spotlight-title {
          font-family: 'Playfair Display', serif;
          font-size: 1.8rem;
          color: var(--home-text);
          margin-bottom: 8px;
        }
        .hero-spotlight-text {
          color: var(--home-muted);
          line-height: 1.7;
          font-size: 0.95rem;
        }
        .hero-spotlight-stat {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 124px;
          border-radius: 22px;
          background: linear-gradient(180deg, var(--home-accent), var(--home-accent-strong));
          color: #052e16;
          box-shadow: 0 14px 30px var(--home-surface-shadow);
        }
        .hero-spotlight-stat span {
          font-size: 0.72rem;
          text-transform: uppercase;
          letter-spacing: 0.12em;
          font-weight: 800;
          opacity: 0.85;
        }
        .hero-spotlight-stat strong {
          font-family: 'Playfair Display', serif;
          font-size: 2rem;
          margin-top: 6px;
        }
        .hero-spotlight-stat em {
          font-size: 0.78rem;
          font-style: normal;
          margin-top: 4px;
          opacity: 0.8;
        }
        .btn-primary {
          background: var(--home-accent); color: #052e16;
          border: none; border-radius: 100px;
          padding: 16px 36px; font-size: 1rem; font-weight: 600;
          cursor: pointer; transition: all 0.2s;
          font-family: 'DM Sans', sans-serif;
          box-shadow: 0 4px 24px var(--home-surface-shadow);
        }
        .btn-primary:hover { background: var(--home-accent-soft); transform: translateY(-2px); box-shadow: 0 8px 32px var(--home-surface-shadow); }
        .btn-secondary {
          background: var(--home-surface-strong); color: var(--home-accent-strong);
          border: 2px solid var(--home-accent-soft); border-radius: 100px;
          padding: 14px 32px; font-size: 1rem; font-weight: 600;
          cursor: pointer; transition: all 0.2s;
          font-family: 'DM Sans', sans-serif;
        }
        .btn-secondary:hover { border-color: var(--home-accent); background: var(--home-surface-alt); transform: translateY(-2px); }

        /* FOREST */
        .forest-scene {
          position: absolute; bottom: -10px; left: 0; right: 0;
          height: 400px; z-index: 1;
        }


        @keyframes contentSlideIn {
          from {
            opacity: 0;
            transform: translateX(42px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        /* FEATURE FLOW */
        .content-overlay {
          position: fixed;
          inset: 0;
          z-index: 50;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 40px 20px;
          background: rgba(0, 0, 0, 0.5);
          backdrop-filter: blur(8px);
          animation: fadeIn 0.3s ease forwards;
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        .content-panel {
          background: var(--home-surface-strong);
          border: 1px solid var(--home-border);
          border-radius: 32px;
          padding: 40px;
          max-width: 900px;
          max-height: 85vh;
          overflow-y: auto;
          box-shadow: 0 24px 80px var(--home-surface-shadow);
          animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(40px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .panel-close {
          position: absolute;
          top: 20px;
          right: 20px;
          background: none;
          border: none;
          font-size: 1.8rem;
          color: var(--home-text);
          cursor: pointer;
          transition: transform 0.2s;
          z-index: 51;
        }
        .panel-close:hover { transform: scale(1.1); }
        .panel-title {
          font-family: 'Playfair Display', serif;
          font-size: clamp(1.8rem, 3vw, 2.8rem);
          line-height: 1.1;
          color: var(--home-text);
          margin-bottom: 24px;
        }
        .panel-text {
          font-size: 1rem;
          line-height: 1.8;
          color: var(--home-muted);
          margin-bottom: 32px;
        }
        .features-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 20px;
          margin-bottom: 24px;
        }
        .feature-card {
          background: var(--home-surface-alt);
          border: 1px solid var(--home-border);
          border-radius: 24px;
          padding: 24px;
          transition: transform 0.2s, box-shadow 0.2s;
        }
        .feature-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 12px 40px var(--home-surface-shadow);
        }
        .feature-icon {
          font-size: 2rem;
          margin-bottom: 12px;
        }
        .feature-title {
          font-size: 1rem;
          font-weight: 600;
          color: var(--home-text);
          margin-bottom: 8px;
        }
        .feature-desc {
          font-size: 0.875rem;
          color: var(--home-muted);
          line-height: 1.6;
        }
        .launch-grid {
          display: grid;
          grid-template-columns: repeat(3, minmax(0, 1fr));
          gap: 12px;
          margin-bottom: 24px;
        }
        .launch-card {
          background: var(--home-surface-alt);
          border: 1px solid var(--home-border);
          border-radius: 22px;
          padding: 18px;
          min-height: 120px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
        }
        .launch-label {
          font-size: 0.72rem;
          font-weight: 700;
          color: var(--home-accent);
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }
        .launch-value {
          font-family: 'Playfair Display', serif;
          font-size: 1.8rem;
          color: var(--home-text);
          margin: 8px 0;
        }
        .launch-sub {
          font-size: 0.8rem;
          color: var(--home-muted);
          line-height: 1.5;
        }
        .action-buttons {
          display: flex;
          gap: 14px;
          flex-wrap: wrap;
          margin-top: 24px;
        }

        /* CTA */
        .cta-section {
          background: linear-gradient(135deg, #14532d 0%, #052e16 100%);
          padding: 100px 40px;
          text-align: center; position: relative; overflow: hidden;
        }
        .cta-section::before {
          content: '';
          position: absolute; inset: 0;
          background: radial-gradient(circle at 30% 50%, rgba(74,222,128,0.15) 0%, transparent 60%),
                      radial-gradient(circle at 70% 50%, rgba(34,197,94,0.1) 0%, transparent 60%);
        }
        .cta-inner { position: relative; z-index: 1; max-width: 600px; margin: 0 auto; }
        .cta-title {
          font-family: 'Playfair Display', serif;
          font-size: clamp(2rem, 4vw, 3rem);
          font-weight: 700; color: white; margin-bottom: 16px;
        }
        .cta-subtitle { color: #86efac; font-size: 1.1rem; margin-bottom: 36px; line-height: 1.6; }

        /* FOOTER */
        .home-footer {
          background: linear-gradient(180deg, rgba(2,6,23,0.96), rgba(2,6,23,1)); padding: 32px 40px;
          display: flex; align-items: center; justify-content: space-between;
          border-top: 1px solid rgba(255,255,255,0.08);
        }
        .footer-logo {
          font-family: 'Playfair Display', serif;
          color: var(--home-accent-soft); font-size: 1.1rem; font-weight: 700;
        }
        .footer-text { font-size: 0.8rem; color: var(--home-accent-soft); opacity: 0.72; }

        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(1.3); }
        }
        @keyframes treeAppear {
          from { opacity: 0; }
          to { opacity: var(--tree-opacity); }
        }
        @keyframes float {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-8px); }
        }
        @keyframes heroDrift {
          0% { transform: translateX(-1.5%); }
          100% { transform: translateX(1.5%); }
        }

        @media (max-width: 768px) {
          .home-nav { padding: 14px 20px; }
          .nav-links { display: none; }
          .nav-actions { gap: 8px; }
          .nav-theme-toggle { min-width: 104px; padding: 9px 12px; }
          .hero { padding: 80px 20px 0; }
          .content-section { padding: 64px 20px; }
          .launch-grid { grid-template-columns: 1fr; }
          .features-grid { grid-template-columns: 1fr; }
          .home-footer { flex-direction: column; gap: 12px; text-align: center; }
          .features-section { padding: 60px 20px; }
          .hero-logo-shell { width: min(62vw, 260px); }
        }
      `}</style>

      {/* Nav */}
      <nav className="home-nav">
        <button
          className="nav-logo"
          onClick={() => navigate("/home")}
          aria-label="Go to home"
          style={{ background: "none", border: "none" }}
        >
          <img src="/logo.svg" alt="Precision Reforestation" className="nav-logo-image" />
          <span>PrecisionReforestation</span>
        </button>
        <div className="nav-actions">
          <div className="nav-links">
            <button
              onClick={() => setActiveView("about")}
              className="nav-link"
              style={{ background: "none", border: "none", cursor: "pointer", font: "inherit" }}
            >
              About
            </button>
            <button
              onClick={() => setActiveView("features")}
              className="nav-link"
              style={{ background: "none", border: "none", cursor: "pointer", font: "inherit" }}
            >
              Features
            </button>
          </div>
          <button
            className="nav-theme-toggle"
            onClick={toggleTheme}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            <span>{theme === "dark" ? "☀ Light" : "☾ Dark"}</span>
          </button>
          <button className="nav-cta" onClick={() => navigate("/dashboard")}>
            Launch Dashboard →
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className="hero">
        <div className="hero-stage">
          <div className={`hero-content ${visible ? "visible" : ""}`}>
            <div className="hero-badge">
              <div className="hero-badge-dot" />
              Nepal Mountain Restoration · AI-Powered
            </div>
            <h1 className="hero-title">
              Restore Nepal's<br />
              <span>Forests</span> with AI
            </h1>
            <p className="hero-subtitle">
              Precision reforestation intelligence combining satellite NDVI, soil data,
              and Claude AI to identify optimal planting sites across Nepal's diverse terrain.
            </p>
            <div className="hero-actions">
              <button className="btn-primary" onClick={() => navigate("/dashboard")}>
                Start Analysis
              </button>
              <button className="btn-secondary" onClick={() => setActiveView("features")}>
                Learn More
              </button>
            </div>
            <div className="hero-spotlight">
              <div className="hero-spotlight-tabs">
                {[
                  ["map", "Map a site"],
                  ["species", "Pick species"],
                  ["dashboard", "Open dashboard"],
                ].map(([key, label]) => (
                  <button
                    key={key}
                    type="button"
                    className={spotlight === key ? "spotlight-tab active" : "spotlight-tab"}
                    onClick={() => setSpotlight(key)}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <div className="hero-spotlight-body">
                <div>
                  <div className="hero-spotlight-label">{spotlightCards[spotlight].label}</div>
                  <div className="hero-spotlight-title">{spotlightCards[spotlight].title}</div>
                  <div className="hero-spotlight-text">{spotlightCards[spotlight].text}</div>
                </div>
                <div className="hero-spotlight-stat">
                  <span>Status</span>
                  <strong>{spotlightCards[spotlight].stat}</strong>
                  <em>interactive preview</em>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Animated Forest */}
        <div className="forest-scene">
          <ForestBackground />
        </div>
      </section>

      {/* About Modal */}
      {activeView === "about" && (
        <div className="content-overlay" onClick={() => setActiveView("hero")}>
          <div className="content-panel" onClick={(e) => e.stopPropagation()}>
            <button className="panel-close" onClick={() => setActiveView("hero")}>×</button>
            <h2 className="panel-title">Data-driven restoration intelligence for Nepal</h2>
            <p className="panel-text">
              PrecisionReforestation combines Sentinel-2 vegetation indices, terrain analysis,
              soil and elevation signals, and AI guidance to help you choose the best planting
              locations and species across Nepal. The experience stays focused on restoration
              outcomes rather than raw data.
            </p>
            <p className="panel-text">
              Our technology leverages satellite imagery at 10-meter resolution, machine learning models
              trained on Nepali ecosystems, and Claude AI to synthesize complex environmental data into
              actionable restoration recommendations. Every analysis accounts for elevation, slope, soil
              composition, and native species viability.
            </p>
            <div className="action-buttons">
              <button className="btn-primary" onClick={() => navigate("/dashboard")}>
                Start Analysis
              </button>
              <button className="btn-secondary" onClick={() => setActiveView("hero")}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Features Modal */}
      {activeView === "features" && (
        <div className="content-overlay" onClick={() => setActiveView("hero")}>
          <div className="content-panel" onClick={(e) => e.stopPropagation()}>
            <button className="panel-close" onClick={() => setActiveView("hero")}>×</button>
            <h2 className="panel-title">Everything for smarter reforestation</h2>
            <p className="panel-text">
              Comprehensive tools built for Nepal's restoration challenges
            </p>
            <div className="features-grid">
              {[
                { icon: "🛰️", title: "Sentinel-2 NDVI", desc: "Real satellite imagery at 10m resolution. Track vegetation health changes across your selected area." },
                { icon: "🌱", title: "Species Matching", desc: "AI matches native Nepali tree species to elevation, slope, soil pH, and climate conditions." },
                { icon: "⚠️", title: "Erosion Analysis", desc: "Slope-driven erosion risk assessment using NASA DEM data. Identifies areas needing stabilization." },
                { icon: "💨", title: "Carbon Potential", desc: "Estimate CO2e sequestration potential based on soil organic matter, NDVI trends, and terrain class." },
                { icon: "🌾", title: "Crop Recommendations", desc: "AI-powered crop suitability analysis for agroforestry integration using real soil and climate data." },
                { icon: "🤖", title: "Claude AI Insights", desc: "Every analysis is synthesized into plain-language restoration guidance tailored to your coordinates." },
              ].map((f) => (
                <div className="feature-card" key={f.title}>
                  <div className="feature-icon">{f.icon}</div>
                  <div className="feature-title">{f.title}</div>
                  <div className="feature-desc">{f.desc}</div>
                </div>
              ))}
            </div>
            <div className="action-buttons">
              <button className="btn-primary" onClick={() => setActiveView("hero")}>
                Home
              </button>
              <button className="btn-secondary" onClick={() => setActiveView("launch")}>
                Launch Dashboard
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Launch Dashboard Modal */}
      {activeView === "launch" && (
        <div className="content-overlay" onClick={() => setActiveView("hero")}>
          <div className="content-panel" onClick={(e) => e.stopPropagation()}>
            <button className="panel-close" onClick={() => setActiveView("hero")}>×</button>
            <h2 className="panel-title">Open the full analysis workspace</h2>
            <p className="panel-text">
              Go from the overview into the actual restoration workflow: map selection, terrain signals,
              environmental context, and AI recommendations in one place.
            </p>
            <div className="launch-grid">
              <div className="launch-card">
                <div className="launch-label">Workflow</div>
                <div className="launch-value">3 steps</div>
                <div className="launch-sub">Select a point, inspect the site, and generate guidance.</div>
              </div>
              <div className="launch-card">
                <div className="launch-label">Coverage</div>
                <div className="launch-value">Nepal</div>
                <div className="launch-sub">Built for mountain terrain, watershed planning, and restoration site scoring.</div>
              </div>
              <div className="launch-card">
                <div className="launch-label">AI output</div>
                <div className="launch-value">Live</div>
                <div className="launch-sub">Instant insights and fallback responses even without an API key.</div>
              </div>
            </div>
            <div className="action-buttons">
              <button className="btn-primary" onClick={() => navigate("/dashboard")}>
                Launch Dashboard →
              </button>
              <button className="btn-secondary" onClick={() => navigate("/species")}>
                Explore Species
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="home-footer">
        <div className="footer-logo">PrecisionReforestation</div>
      </footer>
    </div>
  );
}
