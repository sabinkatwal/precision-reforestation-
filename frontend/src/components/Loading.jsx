export default function Loading({ message = "Loading...", subtext = "Contacting geospatial services" }) {
  return (
    <div className="flex items-center gap-4 px-5 py-4 text-sm text-slate-200" style={{ backgroundColor: "#2d3748", borderRadius: 16 }}>
      <div className="h-10 w-10 rounded-full border border-forest-400/30 border-t-forest-400 animate-spin" />
      <div>
        <div className="font-semibold text-white">{message}</div>
        <div className="text-xs text-slate-400">{subtext}</div>
      </div>
    </div>
  );
}