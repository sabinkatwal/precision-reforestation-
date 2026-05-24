import Navbar from "./components/Navbar.jsx";
import AppRoutes from "./router/index.jsx";

export default function App() {
  return (
    <div className="min-h-screen bg-aurora-grid text-slate-100 relative overflow-x-hidden font-body">
      <div className="pointer-events-none absolute inset-0 opacity-35">
        <div className="absolute -left-24 top-10 h-72 w-72 rounded-full bg-forest-500/20 blur-3xl" />
        <div className="absolute right-[-6rem] top-40 h-96 w-96 rounded-full bg-cyan-500/10 blur-3xl" />
        <div className="absolute bottom-[-8rem] left-1/3 h-80 w-80 rounded-full bg-emerald-500/10 blur-3xl" />
      </div>
      <div className="relative z-10">
        <Navbar />
        <main className="mx-auto w-full max-w-[1700px] px-4 pb-8 pt-4 sm:px-6 lg:px-8">
          <AppRoutes />
        </main>
      </div>
    </div>
  );
}
