import React, { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { Layers, CheckCircle2, Navigation } from "lucide-react";

// Fix Leaflet marker icons in bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// Component to dynamically fit map bounds to active routes
function FitBoundsToRoutes({ routes }) {
  const map = useMap();

  useEffect(() => {
    if (!routes || routes.length === 0) return;

    const allPoints = routes.flatMap((r) => r.coordinates);
    if (allPoints.length > 0) {
      const bounds = L.latLngBounds(allPoints);
      map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
    }
  }, [routes, map]);

  return null;
}

export default function MapView({ routes = [], selectedRouteId, onSelectRoute }) {
  const selectedRoute = routes.find((r) => r.id === selectedRouteId) || routes[0];
  const hasRoutes = Boolean(routes && routes.length > 0 && selectedRoute?.coordinates?.length > 0);

  const originCoord = selectedRoute?.coordinates?.[0] || [28.6315, 77.2167];
  const destCoord = selectedRoute?.coordinates?.[selectedRoute.coordinates.length - 1] || [28.4940, 77.0880];

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl flex flex-col h-[560px] relative">
      {/* Map Header */}
      <div className="px-5 py-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-900/90 z-20">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-bold text-white tracking-wide">
            Interactive Multi-Route Geospatial Map
          </span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400 hidden sm:inline">Leaflet + OpenStreetMap</span>
          <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded-full font-semibold">
            {routes.length} Paths Evaluated
          </span>
        </div>
      </div>

      {/* Leaflet Map Canvas */}
      <div className="relative flex-1 w-full h-full z-10">
        <MapContainer
          center={originCoord}
          zoom={12}
          scrollWheelZoom={true}
          className="w-full h-full"
          style={{ height: "100%", width: "100%" }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          <FitBoundsToRoutes routes={routes} />

          {/* Render Candidate Polylines */}
          {routes.map((route) => {
            const isSelected = route.id === selectedRouteId;
            const isRecommended = route.isRecommended;

            return (
              <React.Fragment key={route.id}>
                {/* Glow/Halo line for currently selected route */}
                {isSelected && (
                  <Polyline
                    positions={route.coordinates}
                    pathOptions={{
                      color: route.color,
                      weight: 9,
                      opacity: 0.35,
                      lineCap: "round",
                    }}
                  />
                )}

                {/* Main route polyline */}
                <Polyline
                  positions={route.coordinates}
                  eventHandlers={{
                    click: () => onSelectRoute && onSelectRoute(route.id),
                  }}
                  pathOptions={{
                    color: route.color,
                    weight: isSelected ? 5.5 : 3.5,
                    opacity: isSelected ? 1.0 : 0.45,
                    dashArray: route.routeCategory === "FAST" && !isSelected ? "6, 6" : undefined,
                    lineCap: "round",
                  }}
                >
                  <Popup>
                    <div className="text-slate-900 p-1">
                      <div className="font-bold text-xs flex items-center gap-1">
                        {route.name}
                        {isRecommended && <span className="text-emerald-600 font-extrabold">(Recommended)</span>}
                      </div>
                      <div className="text-[11px] text-slate-600 mt-1 space-y-0.5">
                        <p>Distance: <strong>{route.distanceKm} km</strong></p>
                        <p>Duration: <strong>{route.durationMin} min</strong></p>
                        <p>Est. CO₂: <strong>{route.co2Grams} g</strong></p>
                        <p>Eco Score: <strong>{route.ecoScore}/100</strong></p>
                      </div>
                    </div>
                  </Popup>
                </Polyline>
              </React.Fragment>
            );
          })}

          {/* Origin & Destination Markers - Only rendered when active routes exist */}
          {hasRoutes && (
            <>
              <Marker position={originCoord}>
                <Popup>
                  <div className="text-slate-900 text-xs">
                    <strong>Origin (Start)</strong>
                  </div>
                </Popup>
              </Marker>

              <Marker position={destCoord}>
                <Popup>
                  <div className="text-slate-900 text-xs">
                    <strong>Destination (End)</strong>
                  </div>
                </Popup>
              </Marker>
            </>
          )}
        </MapContainer>

        {/* Empty state overlay when no routes are active */}
        {!hasRoutes && (
          <div className="absolute inset-0 z-[400] flex items-center justify-center pointer-events-none p-4">
            <div className="bg-slate-900/90 border border-slate-700/80 rounded-2xl p-5 max-w-sm text-center shadow-2xl backdrop-blur">
              <Navigation className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
              <h4 className="text-sm font-bold text-white mb-1">No Active Route Displayed</h4>
              <p className="text-xs text-slate-400">
                Enter valid origin and destination locations above to visualize real-time driving routes on this map.
              </p>
            </div>
          </div>
        )}

        {/* Floating Map Legend - Only shown when routes exist */}
        {hasRoutes && (
          <div className="absolute bottom-4 right-4 z-[400] bg-slate-900/90 backdrop-blur border border-slate-700/80 rounded-xl p-3 shadow-2xl text-xs space-y-1.5 max-w-[210px]">
            <span className="font-semibold text-white block text-[11px] uppercase tracking-wider mb-1">
              Route Legend
            </span>
            {routes.map((r) => (
              <button
                key={r.id}
                onClick={() => onSelectRoute && onSelectRoute(r.id)}
                className={`w-full text-left flex items-center justify-between gap-2 px-1.5 py-1 rounded transition ${
                  r.id === selectedRouteId ? "bg-slate-800 text-white" : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <span className="w-3 h-1.5 rounded-full shrink-0" style={{ backgroundColor: r.color }}></span>
                  <span className="truncate text-[11px]">{r.name}</span>
                </div>
                {r.isRecommended && <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
