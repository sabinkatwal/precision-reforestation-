import { useEffect, useMemo } from "react";
import { MapContainer, Marker, Popup, TileLayer, useMap, useMapEvents } from "react-leaflet";
import L from "leaflet";
import { NEPAL_BOUNDS } from "../services/location.js";
import { useTheme } from "../context/ThemeContext.jsx";

function ClickHandler({ onSelect }) {
  useMapEvents({
    click(event) {
      onSelect({ lat: event.latlng.lat, lng: event.latlng.lng });
    },
  });

  return null;
}

function BoundsHandler() {
  const map = useMap();

  useEffect(() => {
    map.fitBounds(NEPAL_BOUNDS, { padding: [24, 24] });
  }, [map]);

  return null;
}

function ZoomControls() {
  const map = useMap();

  useEffect(() => {
    const control = L.control.zoom({ position: "bottomright" });
    control.addTo(map);

    return () => control.remove();
  }, [map]);

  return null;
}

const selectedIcon = new L.DivIcon({
  className: "",
  html: '<div style="width:18px;height:18px;border-radius:9999px;background:radial-gradient(circle at 35% 35%, #d9ffe8, #22c55e 45%, #15803d 100%);box-shadow:0 0 0 8px rgba(34, 197, 94, 0.12), 0 12px 30px rgba(34, 197, 94, 0.45);border:1px solid rgba(255,255,255,0.45);"></div>',
  iconSize: [18, 18],
  iconAnchor: [9, 9],
});

export default function MapView({ location, onSelect }) {
  const { theme } = useTheme();
  const center = useMemo(() => [28.2, 84.0], []);

  return (
    <div className="glass-panel h-full min-h-[560px] overflow-hidden rounded-[24px] border border-white/10 shadow-[0_24px_80px_rgba(0,0,0,0.35)]">
      <div className="flex items-center justify-between border-b border-white/8 px-5 py-4">
        <div>
          <div className={theme === "dark" ? "font-display text-lg font-bold text-white" : "font-display text-lg font-bold text-slate-900"}>Nepal Restoration Map</div>
          <div className={theme === "dark" ? "text-xs text-slate-400" : "text-xs text-slate-600"}>Click anywhere to analyze a location</div>
        </div>
        <div className={theme === "dark" ? "rounded-full border border-forest-400/20 bg-forest-400/10 px-3 py-1 text-xs text-forest-200" : "rounded-full border border-forest-400/20 bg-forest-50 px-3 py-1 text-xs text-forest-800"}>
          {location.lat.toFixed(4)}, {location.lng.toFixed(4)}
        </div>
      </div>

      <div className="map-shell h-[calc(100%-69px)] min-h-[491px] overflow-hidden rounded-b-[24px]">
        <MapContainer
          center={center}
          zoom={7}
          className="h-full w-full"
          zoomControl={false}
          scrollWheelZoom={true}
          doubleClickZoom={true}
          touchZoom={true}
          zoomSnap={0.5}
          zoomDelta={0.5}
          wheelPxPerZoomLevel={120}
          preferCanvas={true}
          zoomAnimation={true}
          fadeAnimation={true}
          markerZoomAnimation={true}
        >
          <BoundsHandler />
          <ZoomControls />
          <ClickHandler onSelect={onSelect} />
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <Marker position={[location.lat, location.lng]} icon={selectedIcon}>
            <Popup>
              Selected restoration point
              <br />
              {location.lat.toFixed(5)}, {location.lng.toFixed(5)}
            </Popup>
          </Marker>
        </MapContainer>
      </div>
    </div>
  );
}
