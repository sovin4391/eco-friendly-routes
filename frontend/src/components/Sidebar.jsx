import React from 'react';

export default function Sidebar({
  questionCount,
  depth,
  onReset,
  isResetting,
}) {
  return (
    <header className="p-4 sm:p-5 bg-slate-900/90 border-b border-slate-800/80 backdrop-blur-md">
      <div className="max-w-4xl mx-auto flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        {/* Title & Subtitle */}
        <div className="space-y-1">
          <div className="flex items-center gap-3">
            <h1 className="text-xl sm:text-2xl font-black tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-300 bg-clip-text text-transparent">
              QuestionBot
            </h1>
            <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-semibold uppercase tracking-wider">
              Phase 1: Prototype
            </span>
          </div>
          <p className="text-xs text-slate-400">
            The AI that never answers — it only replies with another question.
          </p>
        </div>

        {/* Stats & Controls */}
        <div className="flex items-center gap-3">
          {/* Question Counter */}
          <div className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center gap-2">
            <span className="text-[11px] font-medium text-slate-400">Questions:</span>
            <span className="text-sm font-bold text-indigo-400 font-mono">
              {questionCount}
            </span>
          </div>

          {/* Depth Counter */}
          <div className="px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 flex items-center gap-2">
            <span className="text-[11px] font-medium text-slate-400">Depth:</span>
            <span className="text-sm font-bold text-violet-400 font-mono">
              {depth}
            </span>
          </div>

          {/* Reset Button */}
          <button
            onClick={onReset}
            disabled={isResetting}
            className="px-3.5 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-400 hover:text-rose-300 text-xs font-semibold flex items-center gap-1.5 transition-all active:scale-95 cursor-pointer disabled:opacity-50"
            title="Reset conversation and counters"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className={`h-3.5 w-3.5 ${isResetting ? 'animate-spin' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
            <span>Reset</span>
          </button>
        </div>
      </div>
    </header>
  );
}