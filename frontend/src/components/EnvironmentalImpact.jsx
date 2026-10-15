import React from "react";
import { TreePine, Fuel, TrendingDown, Clock, ShieldCheck, Zap, BatteryCharging, Leaf } from "lucide-react";

export default function EnvironmentalImpact({ savings, vehicleType = "gasoline" }) {
  if (!savings) return null;

  const isEv = savings.isEv || vehicleType.toLowerCase() === "ev";

  // Annual commuter projection (250 commute days, 2 one-way trips)
  const annualCo2Kg = ((savings.co2SavedGrams * 250 * 2) / 1000).toFixed(1);
  const annualFuelLiters = (savings.fuelSavedLiters * 250 * 2).toFixed(1);
  const annualEnergyKwh = ((savings.energySavedKwh || 0) * 250 * 2).toFixed(1);

  return (
    <div className="bg-gradient-to-br from-slate-900 via-emerald-950/20 to-slate-900 border border-emerald-500/30 rounded-2xl p-6 shadow-2xl backdrop-blur relative overflow-hidden">
      {/* Subtle background glow */}
      <div className="absolute -top-24 -right-24 w-60 h-60 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase tracking-wider mb-1">
            <TrendingDown className="w-4 h-4" />
            Ecological Impact Analysis
          </div>
          <h3 className="text-xl font-bold text-white tracking-tight">
            {isEv ? "Energy Optimization by Choosing the Shortest Corridor" : "Emissions Avoided by Choosing the Green Route"}
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Comparative savings vs the baseline fastest expressway alternative
          </p>
        </div>

        {/* Big percentage savings badge */}
        <div className="flex items-baseline gap-2 bg-emerald-500/15 border border-emerald-500/30 px-4 py-2 rounded-2xl w-fit">
          {isEv ? (
            <>
              <span className="text-3xl font-extrabold text-cyan-400 tracking-tight">
                {savings.energyPercentageSaved > 0 ? `-${savings.energyPercentageSaved}%` : "0 g"}
              </span>
              <span className="text-xs font-semibold text-cyan-300">
                {savings.energyPercentageSaved > 0 ? "Energy Saved (kWh)" : "Direct Tailpipe CO₂"}
              </span>
            </>
          ) : (
            <>
              <span className="text-3xl font-extrabold text-emerald-400 tracking-tight">
                -{savings.percentageSaved}%
              </span>
              <span className="text-xs font-semibold text-emerald-300">CO₂ Reduction</span>
            </>
          )}
        </div>
      </div>

      {/* Metrics Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Metric 1 */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Direct Tailpipe CO₂</span>
            <Leaf className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {isEv ? (
              <span className="text-emerald-400">0 <span className="text-sm font-normal text-slate-400">grams</span></span>
            ) : (
              <span>{savings.co2SavedGrams} <span className="text-sm font-normal text-slate-400">grams</span></span>
            )}
          </div>
          <p className="text-[11px] text-emerald-400/90 mt-1">
            {isEv ? "Certified zero direct tailpipe emissions" : `≈ ${savings.co2SavedKg} kg CO₂ saved per one-way trip`}
          </p>
        </div>

        {/* Metric 2 */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">{isEv ? "Electricity Conserved" : "Tree Absorption"}</span>
            {isEv ? <Zap className="w-4 h-4 text-cyan-400" /> : <TreePine className="w-4 h-4 text-teal-400" />}
          </div>
          <div className="text-2xl font-bold text-white">
            {isEv ? (
              <span>{savings.energySavedKwh || 0} <span className="text-sm font-normal text-slate-400">kWh</span></span>
            ) : (
              <span>{savings.treeAbsorptionDays} <span className="text-sm font-normal text-slate-400">days</span></span>
            )}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {isEv ? "Battery electricity saved by shorter travel distance" : "Equal to 1 tree's daily CO₂ absorption"}
          </p>
        </div>

        {/* Metric 3 */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">{isEv ? "Battery Range Retained" : "Fuel Conserved"}</span>
            {isEv ? <BatteryCharging className="w-4 h-4 text-emerald-400" /> : <Fuel className="w-4 h-4 text-yellow-400" />}
          </div>
          <div className="text-2xl font-bold text-white">
            {isEv ? (
              <span>{((savings.energySavedKwh || 0) / 0.18).toFixed(1)} <span className="text-sm font-normal text-slate-400">km range</span></span>
            ) : (
              <span>{savings.fuelSavedLiters} <span className="text-sm font-normal text-slate-400">liters</span></span>
            )}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {isEv ? "Preserved pack range (0.18 kWh/km benchmark)" : "Avoided fuel waste from aerodynamic drag"}
          </p>
        </div>

        {/* Metric 4 */}
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Time Trade-off</span>
            <Clock className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            +{savings.timeTradeoffMin} <span className="text-sm font-normal text-slate-400">min</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1">
            {savings.timeTradeoffMin === 0 ? "Fastest and greenest routes coincide" : "Modest travel difference for maximum eco benefit"}
          </p>
        </div>
      </div>

      {/* Annual Commuter Impact Highlight */}
      <div className="bg-emerald-950/40 border border-emerald-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-emerald-300">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          {isEv ? (
            <span>
              <strong>Annual EV Commuter Projection (250 Days):</strong> Choosing the shorter corridor conserves{" "}
              <span className="text-white font-bold">{annualEnergyKwh} kWh</span> of battery electricity every year with{" "}
              <span className="text-white font-bold">0 g direct tailpipe emissions</span>.
            </span>
          ) : (
            <span>
              <strong>Annual Commuter Projection (250 Days):</strong> Choosing this green route avoids{" "}
              <span className="text-white font-bold">{annualCo2Kg} kg</span> of CO₂ and saves{" "}
              <span className="text-white font-bold">{annualFuelLiters} L</span> of fuel every year.
            </span>
          )}
        </div>
        <span className="text-[10px] text-slate-400 italic">
          *EPA & NRCAN benchmark standards
        </span>
      </div>
    </div>
  );
}
