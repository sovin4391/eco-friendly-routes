import React, { useState } from "react";
import { Navigation, MapPin, Zap, Fuel, Compass, Sparkles, RefreshCw, AlertCircle } from "lucide-react";

export default function RouteForm({ onSubmit, loading, initialValues, onLoadDemo }) {
  const [origin, setOrigin] = useState(initialValues?.origin || "Connaught Place, Central City");
  const [destination, setDestination] = useState(initialValues?.destination || "Cyber Hub, Tech Corridor");
  const [vehicleType, setVehicleType] = useState("gasoline");
  const [travelMode, setTravelMode] = useState("ECO");
  const [formError, setFormError] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    const cleanOrigin = origin.trim();
    const cleanDest = destination.trim();

    if (cleanOrigin.length < 2) {
      setFormError("Source location must be at least 2 characters long.");
      return;
    }
    if (cleanDest.length < 2) {
      setFormError("Destination location must be at least 2 characters long.");
      return;
    }
    if (cleanOrigin.toLowerCase() === cleanDest.toLowerCase()) {
      setFormError("Source and destination cannot be identical.");
      return;
    }

    setFormError(null);
    onSubmit({
      origin: cleanOrigin,
      destination: cleanDest,
      vehicleType,
      travelMode,
    });
  };

  const handleSwap = () => {
    const temp = origin;
    setOrigin(destination);
    setDestination(temp);
    setFormError(null);
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-base font-bold text-white flex items-center gap-2">
          <Navigation className="w-4 h-4 text-emerald-400" />
          Plan Eco Route
        </h2>
        <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-medium">
          OSRM Multi-Route
        </span>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Origin & Destination Inputs */}
        <div className="relative space-y-3">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-emerald-400" />
              Source / Origin Location
            </label>
            <input
              type="text"
              required
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
              placeholder="e.g. Connaught Place, Central City"
              className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
            />
          </div>

          <div className="flex justify-center -my-1.5 relative z-10">
            <button
              type="button"
              onClick={handleSwap}
              title="Swap Locations"
              className="p-1.5 rounded-full bg-slate-800 hover:bg-slate-750 border border-slate-600 text-slate-300 hover:text-white transition shadow cursor-pointer"
            >
              <RefreshCw className="w-3 h-3" />
            </button>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-rose-400" />
              Destination Location
            </label>
            <input
              type="text"
              required
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="e.g. Cyber Hub, Tech Corridor"
              className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
            />
          </div>

          {/* Quick Demo Corridor Shortcuts */}
          <div className="pt-1">
            <span className="text-[10px] text-slate-400 uppercase font-semibold tracking-wider block mb-1.5">
              Quick Test Corridors:
            </span>
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => {
                  setOrigin("Connaught Place");
                  setDestination("Cyber Hub");
                  setFormError(null);
                }}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-750 border border-slate-700 text-slate-300 hover:text-emerald-300 transition cursor-pointer"
              >
                CP &rarr; Cyber Hub
              </button>
              <button
                type="button"
                onClick={() => {
                  setOrigin("India Gate");
                  setDestination("Aerocity");
                  setFormError(null);
                }}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-750 border border-slate-700 text-slate-300 hover:text-emerald-300 transition cursor-pointer"
              >
                India Gate &rarr; Aerocity
              </button>
              <button
                type="button"
                onClick={() => {
                  setOrigin("Hauz Khas");
                  setDestination("Noida Sector 18");
                  setFormError(null);
                }}
                className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-800/80 hover:bg-slate-750 border border-slate-700 text-slate-300 hover:text-emerald-300 transition cursor-pointer"
              >
                Hauz Khas &rarr; Noida
              </button>
            </div>
          </div>
        </div>


        {/* Vehicle & Fuel Selector */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5 text-yellow-400" />
              Vehicle Type
            </label>
            <select
              value={vehicleType}
              onChange={(e) => setVehicleType(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition"
            >
              <option value="gasoline">Passenger Car</option>
              <option value="diesel">Commercial / SUV</option>
              <option value="hybrid">Hybrid Sedan</option>
              <option value="ev">Electric Vehicle (EV)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1 flex items-center gap-1.5">
              <Fuel className="w-3.5 h-3.5 text-blue-400" />
              Fuel / Powertrain
            </label>
            <div className="bg-slate-950/80 border border-slate-700/80 rounded-xl px-3 py-2 text-xs text-slate-300 flex items-center justify-between">
              <span className="capitalize">{vehicleType}</span>
              <span className="text-[10px] text-emerald-400 font-mono">
                {vehicleType === "ev" ? "0g tailpipe" : vehicleType === "hybrid" ? "-45% CO₂" : "Standard"}
              </span>
            </div>
          </div>
        </div>

        {/* Travel Mode Toggle: ECO / BALANCED / FAST */}
        <div className="pt-2">
          <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5 text-emerald-400" />
            Optimization Priority
          </label>
          <div className="grid grid-cols-3 gap-2 bg-slate-950/80 p-1.5 rounded-xl border border-slate-800">
            <button
              type="button"
              onClick={() => setTravelMode("ECO")}
              className={`py-2 px-2 text-xs font-bold rounded-lg transition-all flex flex-col items-center gap-0.5 cursor-pointer ${
                travelMode === "ECO"
                  ? "bg-emerald-600 text-white shadow-md shadow-emerald-950/50"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <span>🌿 ECO</span>
              <span className="text-[9px] opacity-80 font-normal">Min Carbon</span>
            </button>

            <button
              type="button"
              onClick={() => setTravelMode("BALANCED")}
              className={`py-2 px-2 text-xs font-bold rounded-lg transition-all flex flex-col items-center gap-0.5 cursor-pointer ${
                travelMode === "BALANCED"
                  ? "bg-blue-600 text-white shadow-md shadow-blue-950/50"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <span>⚖️ BALANCED</span>
              <span className="text-[9px] opacity-80 font-normal">Time + CO₂</span>
            </button>

            <button
              type="button"
              onClick={() => setTravelMode("FAST")}
              className={`py-2 px-2 text-xs font-bold rounded-lg transition-all flex flex-col items-center gap-0.5 cursor-pointer ${
                travelMode === "FAST"
                  ? "bg-purple-600 text-white shadow-md shadow-purple-950/50"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              <span>⚡ FAST</span>
              <span className="text-[9px] opacity-80 font-normal">Min Time</span>
            </button>
          </div>
        </div>

        {/* Local Validation Error Banner */}
        {formError && (
          <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-xs text-rose-300 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <p>{formError}</p>
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={loading}
          className="w-full mt-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 disabled:opacity-50 text-white font-semibold py-3 px-4 rounded-xl text-sm transition shadow-lg shadow-emerald-950/40 flex items-center justify-center gap-2 cursor-pointer"
        >
          {loading ? (
            <>
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
              Evaluating Alternative Paths...
            </>
          ) : (
            <>
              <Navigation className="w-4 h-4" />
              Find Green Routes
            </>
          )}
        </button>

        {/* Explicit Demo Corridor Action (Requirement 7) */}
        {onLoadDemo && (
          <button
            type="button"
            onClick={() => {
              setOrigin("Connaught Place, Central City");
              setDestination("Cyber Hub, Tech Corridor");
              setFormError(null);
              onLoadDemo();
            }}
            disabled={loading}
            className="w-full bg-slate-800/80 hover:bg-slate-750 border border-slate-700/80 text-slate-300 hover:text-white py-2.5 px-3 rounded-xl text-xs font-semibold transition flex items-center justify-center gap-2 cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            Load Benchmark Demonstration Corridor (CP &rarr; Cyber Hub)
          </button>
        )}
      </form>
    </div>
  );
}
