import React from "react";
import { Leaf, Activity, Sparkles } from "lucide-react";

export default function Navbar({ backendStatus }) {
  const scrollTo = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Branding & Logo */}
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-gradient-to-br from-emerald-400/20 to-teal-500/20 border border-emerald-500/30 rounded-xl text-emerald-400 shadow-inner">
            <Leaf className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-white tracking-tight">
                Eco-Friendly Routes
              </h1>
              <span className="hidden sm:inline-flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-medium">
                <Sparkles className="w-3 h-3" /> PBL Capstone 2026
              </span>
            </div>
            <p className="text-xs text-slate-400">Green Navigation & Carbon Emission Optimizer</p>
          </div>
        </div>

        {/* Section Navigation Links (Desktop) */}
        <nav className="hidden md:flex items-center space-x-1 text-xs">
          <button
            type="button"
            onClick={() => scrollTo("planner")}
            className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition font-medium cursor-pointer"
          >
            Route Planner
          </button>
          <button
            type="button"
            onClick={() => scrollTo("calculator")}
            className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition font-medium cursor-pointer"
          >
            CO₂ Predictor
          </button>
          <button
            type="button"
            onClick={() => scrollTo("vision")}
            className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition font-medium cursor-pointer"
          >
            Road Vision CV
          </button>
          <button
            type="button"
            onClick={() => scrollTo("architecture")}
            className="px-3 py-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800 transition font-medium cursor-pointer"
          >
            System Metrics
          </button>
        </nav>

        {/* Status Indicators */}
        <div className="flex items-center space-x-3">
          {/* Backend REST API Live Status Indicator */}
          <div className="flex items-center space-x-2 bg-slate-800/90 border border-slate-700/70 rounded-full px-3 py-1 text-xs">
            <Activity className="w-3.5 h-3.5 text-slate-400" />
            <span className="text-slate-400 hidden sm:inline">Backend API:</span>
            {backendStatus.loading ? (
              <span className="text-yellow-400 flex items-center gap-1.5 font-medium">
                <span className="w-2 h-2 rounded-full bg-yellow-400 animate-pulse"></span>
                Pinging...
              </span>
            ) : backendStatus.connected ? (
              <span className="text-emerald-400 flex items-center gap-1.5 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                Connected (FastAPI)
              </span>
            ) : (
              <span className="text-rose-400 flex items-center gap-1.5 font-medium">
                <span className="w-2 h-2 rounded-full bg-rose-400"></span>
                Offline (Demo Mode Active)
              </span>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

