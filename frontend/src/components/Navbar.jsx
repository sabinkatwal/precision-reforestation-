import { NavLink } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/biodiversity", label: "Biodiversity" },
  { to: "/erosion", label: "Erosion" },
  { to: "/carbon", label: "Carbon" },
  { to: "/species", label: "Species" },
  { to: "/insight", label: "Insight" },
  { to: "/crops", label: "Crops" },
];

export default function Navbar() {
  return (
    <header className="sticky top-0 z-30 border-b border-white/8 bg-slate-950/70 backdrop-blur-xl">
      <div className="mx-auto flex max-w-[1700px] items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-forest-400/25 bg-forest-500/15 shadow-glow">
            <div className="h-5 w-5 rounded-lg bg-gradient-to-br from-forest-300 to-forest-600" />
          </div>
          <div>
            <div className="font-display text-lg font-bold tracking-tight text-white">
              Ecological Restoration Intelligence
            </div>
            <div className="text-xs uppercase tracking-[0.28em] text-forest-300/80">
              Nepal terrain decision system
            </div>
          </div>
        </div>

        <nav className="hidden items-center gap-2 overflow-x-auto rounded-full border border-white/8 bg-white/5 p-1 text-sm md:flex">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "rounded-full px-4 py-2 transition-all duration-200",
                  isActive
                    ? "bg-forest-500 text-slate-950 shadow-[0_0_0_1px_rgba(255,255,255,0.08)]"
                    : "text-slate-300 hover:bg-white/5 hover:text-white",
                ].join(" ")
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-3 text-xs text-slate-300">
          <span className="rounded-full border border-forest-400/20 bg-forest-400/10 px-3 py-2 text-forest-200">
            Live geospatial + Claude
          </span>
        </div>
      </div>
    </header>
  );
}