import React from "react";
import { Clock, Navigation, CheckCircle2, ChevronRight, Gauge, Mountain, Leaf } from "lucide-react";
import EcoScore from "./EcoScore";

export default function RouteCard({ route, isSelected, onSelect }) {
  const isEco = route.isRecommended || route.routeCategory === "ECO";

  return (
    <div
      onClick={() => onSelect(route.id)}
      className={`relative rounded-2xl p-5 transition-all duration-200 cursor-pointer border ${
        isSelected
          ? "bg-slate-800/90 border-emerald-500 ring-2 ring-emerald-500/30 shadow-xl"
          : "bg-slate-850/60 hover:bg-slate-800/70 border-slate-700/60 hover:border-slate-600 shadow-md"
      }`}
    >
      {/* Top Badges: Rank & Recommendation */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <span
            className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white shadow"
            style={{ backgroundColor: route.color }}
          >
            #{route.rank}
          </span>
          <h4 className="text-sm font-semibold text-white tracking-tight">{route.name}</h4>
        </div>

        <div className="flex items-center gap-1.5 flex-wrap justify-end">
          {route.isRecommended && (
            <span className="inline-flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-semibold shadow-sm">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Recommended Green Choice
            </span>
          )}
          {route.isFastest && !route.isRecommended && (
            <span className="inline-flex items-center gap-1 text-[11px] px-2.5 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/40 font-semibold shadow-sm">
              <Clock className="w-3.5 h-3.5" />
              Fastest Path
            </span>
          )}
        </div>
      </div>

      {/* Route Characteristics / Flow */}
      <p className="text-xs text-slate-400 mb-4 line-clamp-2">{route.routeCharacteristics}</p>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-3 gap-2 mb-4 bg-slate-900/60 rounded-xl p-3 border border-slate-800">
        <div>
          <span className="text-[10px] uppercase tracking-wider text-slate-400 flex items-center gap-1">
            <Navigation className="w-3 h-3 text-slate-500" />
            Distance
          </span>
          <p className="text-sm font-bold text-white mt-0.5">{route.distanceKm} km</p>
        </div>

        <div>
          <span className="text-[10px] uppercase tracking-wider text-slate-400 flex items-center gap-1">
            <Clock className="w-3 h-3 text-slate-500" />
            Duration
          </span>
          <p className="text-sm font-bold text-white mt-0.5">{route.durationMin} min</p>
        </div>

        <div>
          <span className="text-[10px] uppercase tracking-wider text-slate-400 flex items-center gap-1">
            <Leaf className="w-3 h-3 text-emerald-400" />
            {route.co2Grams === 0 && route.energyKwh != null ? "Electricity" : "Tailpipe CO₂"}
          </span>
          <p className={`text-sm font-bold mt-0.5 ${isEco ? "text-emerald-400" : "text-amber-300"}`}>
            {route.co2Grams === 0 && route.energyKwh != null ? (
              <span className="text-cyan-400 font-semibold">{route.energyKwh} kWh</span>
            ) : (
              <span>{route.co2Grams} g</span>
            )}
          </p>
          {route.co2Grams === 0 && route.energyKwh != null && (
            <span className="text-[10px] text-slate-400 block font-normal mt-0.5">
              0 g Tailpipe CO₂
            </span>
          )}
        </div>
      </div>

      {/* Eco Score Display & Selection Footer */}
      <div className="flex items-center justify-between gap-3 pt-2 border-t border-slate-800/80">
        <EcoScore score={route.ecoScore} grade={route.ecoScoreGrade} size="compact" />

        <div className="flex items-center text-xs font-medium text-slate-400 group-hover:text-emerald-400 transition-colors">
          <span className={isSelected ? "text-emerald-400 font-semibold" : ""}>
            {isSelected ? "Active on Map" : "View on Map"}
          </span>
          <ChevronRight className={`w-4 h-4 ml-0.5 transition-transform ${isSelected ? "text-emerald-400 translate-x-1" : ""}`} />
        </div>
      </div>
    </div>
  );
}
