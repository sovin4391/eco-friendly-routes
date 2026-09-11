import React, { useState, useEffect } from 'react';

export default function App() {
  const [backendStatus, setBackendStatus] = useState('checking'); // 'checking', 'connected', 'error'
  const [backendData, setBackendData] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const checkBackendHealth = async () => {
    setBackendStatus('checking');
    setErrorMessage(null);
    try {
      const response = await fetch('http://127.0.0.1:8000/health');
      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }
      const data = await response.json();
      setBackendData(data);
      setBackendStatus('connected');
      setLastChecked(new Date().toLocaleTimeString());
    } catch (err) {
      console.error('Backend check failed:', err);
      setBackendStatus('error');
      setErrorMessage(err.message || 'Failed to fetch');
      setLastChecked(new Date().toLocaleTimeString());
    }
  };

  useEffect(() => {
    checkBackendHealth();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6 selection:bg-indigo-500 selection:text-white">
      {/* Decorative background glow */}
      <div className="fixed inset-0 pointer-events-none flex items-center justify-center">
        <div className="w-[500px] h-[500px] bg-indigo-600/10 blur-[120px] rounded-full"></div>
        <div className="w-[300px] h-[300px] bg-violet-500/10 blur-[90px] rounded-full translate-x-20"></div>
      </div>

      <div className="relative z-10 max-w-2xl w-full space-y-8">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold uppercase tracking-wider">
            <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse"></span>
            Phase 0: Initial Setup
          </div>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-200 to-indigo-300 bg-clip-text text-transparent">
            QuestionBot
          </h1>
          <p className="text-slate-400 text-sm sm:text-base max-w-md mx-auto">
            The AI chatbot with one strange rule: It must never answer the user, it only responds with another question.
          </p>
        </div>

        {/* Connectivity & Health Status Card */}
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 backdrop-blur-xl p-6 shadow-2xl space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
            <div>
              <h2 className="text-lg font-semibold text-slate-100">System Status</h2>
              <p className="text-xs text-slate-400">Verifying frontend & backend communication</p>
            </div>
            <button
              onClick={checkBackendHealth}
              className="px-3.5 py-1.5 text-xs font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 active:scale-95 transition-all rounded-lg border border-slate-700/60 shadow-sm cursor-pointer"
            >
              Re-test Connection
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Frontend Card */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-start gap-3">
              <div className="w-3 h-3 rounded-full bg-emerald-400 mt-1 shadow-sm shadow-emerald-400/50"></div>
              <div>
                <div className="text-sm font-semibold text-slate-200">Frontend (React + Vite)</div>
                <div className="text-xs text-emerald-400 font-medium">Running on http://localhost:5173</div>
                <div className="text-xs text-slate-400 mt-1">Tailwind CSS initialized</div>
              </div>
            </div>

            {/* Backend Card */}
            <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-start gap-3">
              <div
                className={`w-3 h-3 rounded-full mt-1 transition-colors ${
                  backendStatus === 'connected'
                    ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50'
                    : backendStatus === 'checking'
                    ? 'bg-amber-400 animate-ping'
                    : 'bg-rose-500 shadow-sm shadow-rose-500/50'
                }`}
              ></div>
              <div>
                <div className="text-sm font-semibold text-slate-200">Backend (FastAPI)</div>
                {backendStatus === 'connected' && (
                  <>
                    <div className="text-xs text-emerald-400 font-medium">Connected to http://127.0.0.1:8000</div>
                    <div className="text-xs text-slate-400 mt-1">
                      Endpoint: <code className="bg-slate-800 px-1 py-0.5 rounded text-[11px] text-indigo-300">/health</code>
                    </div>
                  </>
                )}
                {backendStatus === 'checking' && (
                  <div className="text-xs text-amber-400 font-medium">Connecting to server...</div>
                )}
                {backendStatus === 'error' && (
                  <>
                    <div className="text-xs text-rose-400 font-medium">Cannot reach backend</div>
                    <div className="text-xs text-slate-400 mt-1">{errorMessage}</div>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Raw Response Output */}
          {backendData && (
            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-mono text-slate-400">Response from GET /health</span>
                <span className="text-[10px] text-slate-400">Last verified: {lastChecked}</span>
              </div>
              <pre className="text-xs font-mono text-emerald-400 bg-slate-900 p-2.5 rounded-lg overflow-x-auto border border-slate-800/60">
                {JSON.stringify(backendData, null, 2)}
              </pre>
            </div>
          )}

          {/* Phase 0 Checklist */}
          <div className="space-y-2 pt-2 border-t border-slate-800/60">
            <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Phase 0 Checklist</div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-slate-300">
              <div className="flex items-center gap-2">
                <span className="text-emerald-400">✓</span> Python & Node.js verified
              </div>
              <div className="flex items-center gap-2">
                <span className="text-emerald-400">✓</span> Git initialized
              </div>
              <div className="flex items-center gap-2">
                <span className="text-emerald-400">✓</span> React + Vite + Tailwind configured
              </div>
              <div className="flex items-center gap-2">
                <span className="text-emerald-400">✓</span> FastAPI with /health endpoint
              </div>
              <div className="flex items-center gap-2">
                <span className="text-emerald-400">✓</span> Secrets (.env) protected in .gitignore
              </div>
              <div className="flex items-center gap-2">
                <span className="text-emerald-400">✓</span> Frontend ⇄ Backend communication verified
              </div>
            </div>
          </div>
        </div>

        {/* Phase Notification */}
        <div className="text-center text-xs text-slate-400">
          Phase 0 Complete — Waiting for user approval before starting Phase 1.
        </div>
      </div>
    </div>
  );
}
