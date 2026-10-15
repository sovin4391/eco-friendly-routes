import React from "react";
import { Award, Leaf } from "lucide-react";

export default function EcoScore({ score = 90, grade = "A", size = "normal" }) {
  // Determine color styling based on score threshold
  const getColorScheme = (val) => {
    if (val >= 85) {
      return {
        text: "text-emerald-400",
        bg: "bg-emerald-500/10",
        border: "border-emerald-500/30",
        ring: "stroke-emerald-500",
        badge: "bg-emerald-500 text-slate-950",
        label: "Superior Eco Efficiency",
      };
    } else if (val >= 70) {
      return {
        text: "text-blue-400",
        bg: "bg-blue-500/10",
        border: "border-blue-500/30",
        ring: "stroke-blue-500",
        badge: "bg-blue-500 text-white",
        label: "Moderate Eco Efficiency",
      };
    } else {
      return {
        text: "text-amber-400",
        bg: "bg-amber-500/10",
        border: "border-amber-500/30",
        ring: "stroke-amber-500",
        badge: "bg-amber-500 text-slate-950",
        label: "Standard / High Emissions",
      };
    }
  };

  const scheme = getColorScheme(score);

  if (size === "compact") {
    return (
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border ${scheme.border} ${scheme.bg}`}>
        <Leaf className={`w-3.5 h-3.5 ${scheme.text}`} />
        <span className="text-xs font-bold text-white">{score}</span>
        <span className="text-[10px] text-slate-400">/100</span>
        <span className={`text-[10px] px-1 rounded font-bold ${scheme.badge}`}>{grade}</span>
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-3 p-3 rounded-xl border ${scheme.border} ${scheme.bg}`}>
      {/* Mini SVG Progress Ring */}
      <div className="relative w-12 h-12 flex items-center justify-center shrink-0">
        <svg className="w-12 h-12 -rotate-90" viewBox="0 0 36 36">
          <path
            className="stroke-slate-700/60"
            strokeWidth="3.5"
            fill="none"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          />
          <path
            className={`${scheme.ring} transition-all duration-700 ease-out`}
            strokeDasharray={`${score}, 100`}
            strokeWidth="3.5"
            strokeLinecap="round"
            fill="none"
            d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-bold text-white">{score}</span>
        </div>
      </div>

      <div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs font-semibold text-slate-200">Eco Score</span>
          <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${scheme.badge}`}>{grade}</span>
        </div>
        <p className="text-[11px] text-slate-400">{scheme.label}</p>
      </div>
    </div>
  );
}
