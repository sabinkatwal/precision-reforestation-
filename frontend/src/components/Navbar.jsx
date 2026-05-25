import { NavLink } from "react-router-dom";
import { useTheme } from "../context/ThemeContext.jsx";

const navItems = [
  { to: "/home", label: "Home" },
  { to: "/", label: "Dashboard" },
  { to: "/biodiversity", label: "Biodiversity" },
  { to: "/erosion", label: "Erosion" },
  { to: "/carbon", label: "Carbon" },
  { to: "/species", label: "Species" },
  { to: "/insight", label: "Insight" },
  { to: "/crops", label: "Crops" },
];

export default function Navbar() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <header
      className="sticky top-0 z-30 border-b backdrop-blur-xl"
      style={{
        backgroundColor: isDark ? "rgba(2, 6, 23, 0.86)" : "rgba(247, 250, 245, 0.9)",
        borderColor: isDark ? "rgba(148, 163, 184, 0.14)" : "rgba(22, 163, 74, 0.14)",
      }}
    >
      <div className="mx-auto flex max-w-[1700px] items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <NavLink
          to="/"
          end
          className={({ isActive }) => [
            "group flex min-w-0 items-center gap-3 rounded-2xl px-2.5 py-2 transition-all duration-200",
            isActive ? "bg-white/5 shadow-[0_10px_28px_rgba(34,197,94,0.08)]" : "hover:bg-white/5 hover:shadow-[0_10px_28px_rgba(34,197,94,0.08)]",
          ].join(" ")}
          aria-label="Go to homepage"
        >
          <div className={isDark ? "flex h-10 w-10 flex-none items-center justify-center rounded-2xl border border-white/10 bg-white/5 shadow-glow transition-transform duration-200 group-hover:scale-[1.03] group-hover:shadow-[0_0_24px_rgba(45,212,191,0.18)]" : "flex h-10 w-10 flex-none items-center justify-center rounded-2xl border border-forest-400/20 bg-white shadow-glow transition-transform duration-200 group-hover:scale-[1.03] group-hover:shadow-[0_0_24px_rgba(22,163,74,0.18)]"}>
            <img src="/logo.png" alt="Precision Reforestation" className="h-7 w-7 object-contain" style={{ filter: isDark ? "brightness(1.08)" : "brightness(0.92)" }} />
          </div>
          <div className="min-w-0">
            <div className={isDark ? "font-display text-[1.05rem] font-bold tracking-tight text-white transition-colors duration-200 group-hover:text-forest-100" : "font-display text-[1.05rem] font-bold tracking-tight text-slate-900 transition-colors duration-200 group-hover:text-forest-700"}>
              Ecological Restoration Intelligence
            </div>
            <div className={isDark ? "text-[11px] uppercase tracking-[0.28em] text-forest-300/80" : "text-[11px] uppercase tracking-[0.28em] text-forest-700/80"}>
              Nepal terrain decision system
            </div>
          </div>
        </NavLink>

        <nav className={isDark ? "hidden max-w-[58vw] items-center gap-1 overflow-x-auto rounded-full border border-white/10 bg-white/5 p-1 text-sm md:flex lg:gap-2" : "hidden max-w-[58vw] items-center gap-1 overflow-x-auto rounded-full border border-forest-400/15 bg-white/70 p-1 text-sm md:flex lg:gap-2"}>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                [
                  "rounded-full px-4 py-2.5 whitespace-nowrap transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-forest-400/40",
                  isActive
                    ? "bg-forest-500 text-slate-950 shadow-[0_12px_32px_rgba(34,197,94,0.22)] scale-[1.02]"
                    : isDark
                      ? "text-slate-300 hover:bg-white/5 hover:text-white hover:-translate-y-[1px]"
                      : "text-slate-600 hover:bg-forest-50 hover:text-forest-700 hover:-translate-y-[1px]",
                ].join(" ")
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex flex-wrap items-center justify-end gap-3 text-xs text-slate-300">
          <button
            type="button"
            onClick={toggleTheme}
            className={isDark
              ? "rounded-full border border-white/10 bg-white/5 px-3 py-2 text-slate-100 transition hover:-translate-y-[1px] hover:bg-white/10"
              : "rounded-full border border-forest-400/20 bg-white px-3 py-2 text-slate-900 transition hover:-translate-y-[1px] hover:bg-forest-50"
            }
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
          >
            {theme === "dark" ? "☀ Light mode" : "☾ Dark mode"}
          </button>
          <span className={isDark ? "rounded-full border border-forest-400/20 bg-forest-400/10 px-3 py-2 text-forest-200" : "rounded-full border border-forest-400/20 bg-forest-50 px-3 py-2 text-forest-800"}>
            Live geospatial + Claude
          </span>
        </div>
      </div>
    </header>
  );
}