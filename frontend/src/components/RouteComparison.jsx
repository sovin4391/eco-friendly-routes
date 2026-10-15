import React from "react";
import { ArrowUpDown, Check, Zap, Clock, Navigation, Leaf, Gauge } from "lucide-react";

export default function RouteComparison({ routes = [], selectedRouteId, onSelectRoute }) {
  if (!routes || routes.length === 0) return null;

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <ArrowUpDown className="w-4 h-4 text-emerald-400" />
            Route Comparison Matrix
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Side-by-side trade-off analysis across distance, duration, and carbon impact
          </p>
        </div>
        <span className="text-[11px] px-2.5 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700 w-fit">
          Direct Multi-Route Benchmarking
        </span>
      </div>

      {/* Comparison Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 text-slate-400">
              <th className="py-3 px-3 font-semibold">Route Option</th>
              <th className="py-3 px-3 font-semibold">Priority</th>
              <th className="py-3 px-3 font-semibold">Distance</th>
              <th className="py-3 px-3 font-semibold">Travel Time</th>
              <th className="py-3 px-3 font-semibold">Est. CO₂</th>
              <th className="py-3 px-3 font-semibold">Eco Score</th>
              <th className="py-3 px-3 font-semibold">Traffic Flow</th>
              <th className="py-3 px-3 font-semibold text-right">Selection</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {routes.map((route) => {
              const isSelected = route.id === selectedRouteId;
              const isRecommended = route.isRecommended;

              return (
                <tr
                  key={route.id}
                  onClick={() => onSelectRoute && onSelectRoute(route.id)}
                  className={`transition-colors cursor-pointer ${
                    isSelected
                      ? "bg-emerald-500/10 hover:bg-emerald-500/15"
                      : "hover:bg-slate-800/40"
                  }`}
                >
                  {/* Route Name & Color Marker */}
                  <td className="py-3.5 px-3">
                    <div className="flex items-center gap-2 font-semibold text-white">
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: route.color }}
                      ></span>
                      {route.name}
                    </div>
                  </td>

                  {/* Priority Tag */}
                  <td className="py-3.5 px-3">
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                        route.routeCategory === "ECO"
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                          : route.routeCategory === "FAST"
                          ? "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                          : "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                      }`}
                    >
                      {route.routeCategory}
                    </span>
                  </td>

                  {/* Distance */}
                  <td className="py-3.5 px-3 font-medium text-slate-200">
                    {route.distanceKm} km
                  </td>

                  {/* Time */}
                  <td className="py-3.5 px-3 font-medium text-slate-200">
                    {route.durationMin} min
                  </td>

                  {/* CO2 Emissions & Energy */}
                  <td className="py-3.5 px-3">
                    <div className="font-bold">
                      <span className={isRecommended ? "text-emerald-400" : "text-amber-300"}>
                        {route.co2Grams} g
                      </span>
                    </div>
                    {route.energyKwh != null && (
                      <div className="text-[10px] text-cyan-400 font-medium mt-0.5 flex items-center gap-1">
                        <Zap className="w-3 h-3 shrink-0" />
                        {route.energyKwh} kWh
                      </div>
                    )}
                  </td>

                  {/* Eco Score */}
                  <td className="py-3.5 px-3">
                    <span className="font-bold text-white">{route.ecoScore}</span>
                    <span className="text-slate-500 text-[10px]">/100</span>
                    <span className="ml-1.5 text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                      {route.ecoScoreGrade}
                    </span>
                  </td>

                  {/* Traffic Flow */}
                  <td className="py-3.5 px-3 text-slate-400">
                    {route.congestionLevel}
                  </td>

                  {/* Select Button */}
                  <td className="py-3.5 px-3 text-right">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onSelectRoute(route.id);
                      }}
                      className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                        isSelected
                          ? "bg-emerald-500 text-slate-950 font-bold"
                          : "bg-slate-800 hover:bg-slate-700 text-slate-300"
                      }`}
                    >
                      {isSelected ? "Active" : "Select"}
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
