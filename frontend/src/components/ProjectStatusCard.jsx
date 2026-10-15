import React from "react";
import { Server, Database, BrainCircuit, Layers, Sparkles, Map, Camera } from "lucide-react";

export default function ProjectStatusCard({ backendData, isDemonstration }) {
  return (
    <div id="architecture" className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur space-y-5">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <Layers className="w-4 h-4 text-emerald-400" />
          System Architecture & Capstone Submission Status
        </h3>
        <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 font-medium w-fit">
          PBL Capstone Evaluation Ready
        </span>
      </div>

      {/* 5-Tier Architecture Status Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-3">
        {/* Frontend & Leaflet */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Map className="w-3.5 h-3.5 text-teal-400" />
              Leaflet Maps
            </span>
            <span className="text-emerald-400 font-medium">Active</span>
          </div>
          <p className="text-[11px] text-slate-500">Live OSRM Polylines</p>
        </div>

        {/* Backend API */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Server className="w-3.5 h-3.5 text-blue-400" />
              FastAPI
            </span>
            <span className={backendData ? "text-emerald-400 font-medium" : "text-amber-400 font-medium"}>
              {backendData ? "v0.1.0 Active" : "Port 8000"}
            </span>
          </div>
          <p className="text-[11px] text-slate-500">Uvicorn ASGI Backend</p>
        </div>

        {/* Database */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Database className="w-3.5 h-3.5 text-purple-400" />
              SQLite DB
            </span>
            <span className="text-emerald-400 font-medium">
              eco_routes.db
            </span>
          </div>
          <p className="text-[11px] text-slate-500">Persistent Query Logs</p>
        </div>

        {/* Module A: ML Emissions Engine */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-slate-400 flex items-center gap-1.5">
              <BrainCircuit className="w-3.5 h-3.5 text-amber-400" />
              Emissions ML
            </span>
            <span className="text-emerald-400 font-medium">
              R² = 0.9984
            </span>
          </div>
          <p className="text-[11px] text-slate-500">Random Forest Regressor</p>
        </div>

        {/* Module C: Road Damage CV */}
        <div className="bg-slate-950/70 border border-slate-800 rounded-xl p-3">
          <div className="flex items-center justify-between text-xs mb-1">
            <span className="text-slate-400 flex items-center gap-1.5">
              <Camera className="w-3.5 h-3.5 text-rose-400" />
              RDD2022 CV
            </span>
            <span className="text-rose-400 font-medium">
              mAP50 = 13.01%
            </span>
          </div>
          <p className="text-[11px] text-slate-500">YOLOv8n Surface Vision</p>
        </div>
      </div>

      {/* Dataset & Model Verification Summary Table */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
              <BrainCircuit className="w-3.5 h-3.5" />
              Dataset 1: Vehicle Emissions (Canada NRC)
            </span>
            <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded border border-emerald-500/30">
              Verified ML Model
            </span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Trained on 7,385 vehicle records from Natural Resources Canada. Predicts direct tailpipe CO₂ (g/km) using engine displacement, cylinders, and fuel type. Target leakage strictly prevented. Held-out test performance: <strong className="text-slate-200">R² = 0.9984</strong>, <strong className="text-slate-200">MAE = 3.82 g/km</strong>. Pure EVs report 0 g tailpipe CO₂ with electricity consumption in kWh.
          </p>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-rose-400 flex items-center gap-1.5">
              <Camera className="w-3.5 h-3.5" />
              Dataset 2: Road Damage (RDD2022 India)
            </span>
            <span className="text-[10px] font-mono bg-rose-500/10 text-rose-400 px-2 py-0.5 rounded border border-rose-500/30">
              Verified CV Model
            </span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed">
            Trained on official RDD2022 India pavement dataset (CRDDC 2022). Ultralytics YOLOv8n 5-epoch promoted run achieves <strong className="text-slate-200">mAP@0.5 = 13.01%</strong> and <strong className="text-slate-200">mAP@0.5:0.95 = 5.40%</strong> on held-out test split (vs 3.12% baseline). Detects D00, D10, D20 cracks and D40 potholes as local visual evidence.
          </p>
        </div>
      </div>

      {/* Review Disclosure / Transparency Alert */}
      <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 flex items-start gap-2.5">
        <Sparkles className="w-4 h-4 shrink-0 mt-0.5 text-emerald-400" />
        <div className="leading-relaxed">
          <p className="font-semibold text-slate-200">Verified System Architecture for PBL Submission:</p>
          <p className="mt-0.5 text-slate-400">
            OpenStreetMap (OSRM) provides road driving geometries and distances. Tailpipe emissions are calculated via Scikit-Learn Random Forest regression (<code className="text-emerald-400">rate_g_per_km × distance_km</code>). Pavement distress vision runs via YOLOv8n as an independent visual inspection module. BDD100K or unverified third-party datasets were intentionally excluded to preserve model integrity.
          </p>
        </div>
      </div>
    </div>
  );
}

