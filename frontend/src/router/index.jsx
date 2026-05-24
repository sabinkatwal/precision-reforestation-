import { Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "../pages/Dashboard.jsx";
import Home from "../pages/Home.jsx";
import Biodiversity from "../pages/Biodiversity.jsx";
import Erosion from "../pages/Erosion.jsx";
import Carbon from "../pages/Carbon.jsx";
import Species from "../pages/Species.jsx";
import Insight from "../pages/Insight.jsx";
import Crops from "../pages/Crops.jsx";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/home" element={<Home />} />
      <Route path="/biodiversity" element={<Biodiversity />} />
      <Route path="/erosion" element={<Erosion />} />
      <Route path="/carbon" element={<Carbon />} />
      <Route path="/species" element={<Species />} />
      <Route path="/insight" element={<Insight />} />
      <Route path="/crops" element={<Crops />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}