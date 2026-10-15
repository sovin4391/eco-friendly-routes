import React, { useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import RouteForm from "./components/RouteForm";
import MapView from "./components/MapView";
import RouteCard from "./components/RouteCard";
import RouteComparison from "./components/RouteComparison";
import EnvironmentalImpact from "./components/EnvironmentalImpact";
import ProjectStatusCard from "./components/ProjectStatusCard";
import EmissionsCalculatorCard from "./components/EmissionsCalculatorCard";
import RoadDamageCard from "./components/RoadDamageCard";
import { checkBackendHealth, fetchRouteRecommendations, getExplicitDemonstrationRoutes } from "./services/api";
import { Sparkles, Route, Info, AlertCircle } from "lucide-react";

export default function App() {
  const [backendStatus, setBackendStatus] = useState({
    loading: true,
    connected: false,
    data: null,
  });

  const [routes, setRoutes] = useState([]);
  const [selectedRouteId, setSelectedRouteId] = useState(null);
  const [savings, setSavings] = useState(null);
  const [isDemonstration, setIsDemonstration] = useState(false);
  const [vehicleType, setVehicleType] = useState("gasoline");
  const [loading, setLoading] = useState(false);
  const [routeNotice, setRouteNotice] = useState(null);
  const [limitationsNote, setLimitationsNote] = useState(null);
  const [searchError, setSearchError] = useState(null);
  const [searchParams, setSearchParams] = useState({
    origin: "Connaught Place, Central City",
    destination: "Cyber Hub, Tech Corridor",
  });

  // Explicit demo corridor loader (Requirement 7)
  const handleLoadDemo = () => {
    setLoading(true);
    setSearchError(null);
    const demoData = getExplicitDemonstrationRoutes(vehicleType, "ECO");
    setRoutes(demoData.routes);
    setSavings(demoData.savings);
    setIsDemonstration(true);
    setRouteNotice(demoData.notice);
    setLimitationsNote(demoData.limitationsNote);
    setSearchParams({
      origin: demoData.origin,
      destination: demoData.destination,
    });
    if (demoData.routes.length > 0) {
      setSelectedRouteId(demoData.routes[0].id);
    }
    setLoading(false);
  };

  // Initial load: Check backend health and load initial routes
  useEffect(() => {
    async function init() {
      // 1. Check live FastAPI backend health
      const healthRes = await checkBackendHealth();
      setBackendStatus({
        loading: false,
        connected: healthRes.connected,
        data: healthRes.data,
      });

      // 2. Load initial route recommendations
      setLoading(true);
      const res = await fetchRouteRecommendations({
        origin: searchParams.origin,
        destination: searchParams.destination,
        vehicleType: "gasoline",
        travelMode: "ECO",
      });

      if (res.success && res.routes && res.routes.length > 0) {
        setRoutes(res.routes);
        setSavings(res.savings || null);
        setIsDemonstration(false);
        setRouteNotice(res.notice || null);
        setLimitationsNote(res.limitationsNote || null);
        const rec = res.routes.find((r) => r.isRecommended) || res.routes[0];
        setSelectedRouteId(rec.id);
      } else {
        // If initial backend call is unavailable on startup, explicitly load demo
        handleLoadDemo();
      }
      setLoading(false);
    }

    init();

    // Periodic health ping
    const interval = setInterval(async () => {
      const healthRes = await checkBackendHealth();
      setBackendStatus({
        loading: false,
        connected: healthRes.connected,
        data: healthRes.data,
      });
    }, 15000);

    return () => clearInterval(interval);
  }, []);

  // Handle route search submissions
  const handleRouteSearch = async (formValues) => {
    setLoading(true);
    setSearchError(null);
    setVehicleType(formValues.vehicleType);
    setSearchParams({
      origin: formValues.origin,
      destination: formValues.destination,
    });

    try {
      const res = await fetchRouteRecommendations(formValues);
      if (res.success && res.routes && res.routes.length > 0) {
        setRoutes(res.routes);
        setSavings(res.savings || null);
        setIsDemonstration(false);
        setRouteNotice(res.notice || null);
        setLimitationsNote(res.limitationsNote || null);
        setSearchError(null);
        const rec = res.routes.find((r) => r.isRecommended) || res.routes[0];
        setSelectedRouteId(rec.id);
      } else {
        // Clear all old route results when request fails (Requirement 6)
        setRoutes([]);
        setSavings(null);
        setSelectedRouteId(null);
        setRouteNotice(null);
        setIsDemonstration(false);
        setSearchError(res.error || "Route could not be calculated for the given endpoints.");
      }
    } catch (err) {
      setRoutes([]);
      setSavings(null);
      setSelectedRouteId(null);
      setRouteNotice(null);
      setIsDemonstration(false);
      setSearchError(err.message || "An unexpected error occurred while calculating routes.");
    } finally {
      setLoading(false);
    }
  };

  const selectedRoute = routes.find((r) => r.id === selectedRouteId) || routes[0];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-slate-950">
      <Navbar backendStatus={backendStatus} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Project Header Banner */}
        <div className="bg-gradient-to-r from-emerald-950/80 via-slate-900 to-slate-900 border border-emerald-500/30 rounded-3xl p-6 sm:p-8 shadow-2xl flex flex-col md:flex-row items-start md:items-center justify-between gap-6 relative overflow-hidden">
          <div className="relative z-10 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold uppercase tracking-wider mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              Machine Learning Capstone Project &bull; PBL Final Evaluation
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
              Eco-Friendly Routes
            </h2>
            <p className="text-sm sm:text-base text-slate-300 mt-2 leading-relaxed">
              Intelligent multi-route optimization comparing candidate paths and evaluating greenhouse gas emissions (CO₂ grams) and energy consumption. Prioritize planetary sustainability alongside travel time efficiency.
            </p>
          </div>

          <div className="relative z-10 flex flex-col sm:flex-row md:flex-col gap-2 shrink-0">
            <div className="bg-slate-900/90 border border-slate-700/80 rounded-2xl px-4 py-3 text-xs">
              <span className="text-slate-400 block text-[10px] uppercase font-semibold">Active Corridor</span>
              <span className="text-white font-bold text-sm truncate max-w-[220px] block mt-0.5">
                {searchParams.origin}
              </span>
              <span className="text-emerald-400 block text-[10px] font-mono mt-0.5">
                &darr; {searchParams.destination}
              </span>
            </div>
          </div>
        </div>

        {/* System Architecture & Review Status */}
        <ProjectStatusCard
          backendData={backendStatus.data}
          isDemonstration={isDemonstration}
        />

        {/* Live Scikit-Learn Vehicle CO2 Estimator (Real ML Pipeline Inference) */}
        <div id="calculator">
          <EmissionsCalculatorCard
            selectedRouteDistance={selectedRoute?.distanceKm || 25.0}
            activeVehicleType={vehicleType}
          />
        </div>

        {/* Main Interactive Workspace: Search & Map */}
        <div id="planner" className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Form & Route Cards */}
          <div className="lg:col-span-5 space-y-6">

            <RouteForm
              onSubmit={handleRouteSearch}
              loading={loading}
              initialValues={searchParams}
              onLoadDemo={handleLoadDemo}
            />

            {/* Search Validation & Routing Error Alert Banner */}
            {searchError && (
              <div className="p-4 rounded-2xl bg-rose-950/40 border border-rose-500/50 text-xs text-rose-200 flex items-start gap-3 shadow-lg">
                <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <span className="font-bold text-rose-300 uppercase tracking-wider text-[11px] block">
                    Location & Routing Validation Error
                  </span>
                  <p className="leading-relaxed">{searchError}</p>
                </div>
              </div>
            )}

            {/* Scientific Estimation Methodology Notice */}
            <div className="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 text-xs text-slate-300 space-y-1 shadow-md">
              <div className="flex items-center gap-1.5 font-semibold text-emerald-400 text-[11px] uppercase tracking-wider">
                <Info className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                Estimation Methodology
              </div>
              <p className="text-slate-400 text-xs leading-relaxed">
                {limitationsNote || "Route emissions represent certified direct tailpipe CO₂ (predicted rate g/km × distance km). Real-time traffic congestion, signal wait delays, and elevation gradients are unverified and excluded."}
              </p>
            </div>

            {/* Routing Engine Notice / Status */}
            {routeNotice && (
              <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-400 flex items-start gap-2 shadow">
                <Info className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <p className="leading-relaxed">{routeNotice}</p>
              </div>
            )}

            {/* Candidate Route Cards List */}
            <div className="space-y-3">
              <div className="flex items-center justify-between px-1">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <Route className="w-4 h-4 text-emerald-400" />
                  Candidate Route Results ({routes.length})
                </h3>
                <span className="text-[11px] text-slate-400">Click card to highlight</span>
              </div>

              {loading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 animate-pulse h-36"></div>
                  ))}
                </div>
              ) : routes.length > 0 ? (
                <div className="space-y-3">
                  {routes.map((route) => (
                    <RouteCard
                      key={route.id}
                      route={route}
                      isSelected={route.id === selectedRouteId}
                      onSelect={(id) => setSelectedRouteId(id)}
                    />
                  ))}
                </div>
              ) : (
                <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 text-center text-xs text-slate-400 space-y-1.5">
                  <p className="font-semibold text-slate-300">No active route results.</p>
                  <p className="text-[11px] text-slate-500">
                    {searchError
                      ? "Previous route results were cleared due to validation error. Correct the endpoints above and try again."
                      : "Enter valid source and destination locations above to evaluate eco-friendly routes."}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Interactive Leaflet Map */}
          <div className="lg:col-span-7 space-y-6">
            <MapView
              routes={routes}
              selectedRouteId={selectedRouteId}
              onSelectRoute={(id) => setSelectedRouteId(id)}
            />
          </div>
        </div>

        {/* Environmental Impact Savings Section */}
        {routes.length > 0 && (
          <EnvironmentalImpact
            savings={savings}
            vehicleType={vehicleType}
          />
        )}

        {/* Multi-Route Side-by-Side Comparison Matrix */}
        {routes.length > 0 && (
          <RouteComparison
            routes={routes}
            selectedRouteId={selectedRouteId}
            onSelectRoute={(id) => setSelectedRouteId(id)}
          />
        )}

        {/* Module C: Road Damage & Pothole Vision Analysis */}
        <RoadDamageCard />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-950 py-6 mt-12 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p>
            Eco-Friendly Routes &bull; Machine Learning PBL Capstone 2026 &bull; Final Submission
          </p>
          <p className="text-slate-600">
            Powered by React, Tailwind CSS, Leaflet, FastAPI, Scikit-Learn & YOLOv8
          </p>
        </div>
      </footer>
    </div>
  );
}

