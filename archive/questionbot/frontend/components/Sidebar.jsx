import React from 'react';

const PERSONALITIES = [
  { id: 'NORMAL', emoji: '🧠', name: 'NORMAL', desc: 'Just questions.' },
  { id: 'SARCASTIC', emoji: '😏', name: 'SARCASTIC', desc: 'Questions, but with attitude.' },
  { id: 'PHILOSOPHICAL', emoji: '🌌', name: 'PHILOSOPHICAL', desc: 'Questions about the questions.' },
  { id: 'EXISTENTIAL', emoji: '💀', name: 'EXISTENTIAL', desc: "Questions that probably shouldn't be asked." },
  { id: 'CHAOTIC', emoji: '🌀', name: 'CHAOTIC', desc: 'Nobody knows where this is going.' },
];

export default function Sidebar({
  personality,
  onSelectPersonality,
  isBreakMode,
  onToggleBreakMode,
  questionCount,
  depth,
  depthTitle = 'UNINITIATED',
  breakAttempts,
  questionsSurvived,
  unlockedAchievementsCount = 0,
  totalAchievementsCount = 5,
  onOpenAchievements,
  onOpenStats,
  onReset,
  isResetting,
}) {
  // Determine progression color based on depth
  const getDepthColor = () => {
    if (depth >= 10) return 'from-rose-500 to-purple-500 border-rose-500/40 text-rose-300';
    if (depth >= 8) return 'from-purple-500 to-indigo-500 border-purple-500/40 text-purple-300';
    if (depth >= 5) return 'from-amber-500 to-orange-500 border-amber-500/40 text-amber-300';
    if (depth >= 3) return 'from-blue-500 to-cyan-500 border-blue-500/40 text-blue-300';
    if (depth >= 1) return 'from-emerald-500 to-teal-500 border-emerald-500/40 text-emerald-300';
    return 'from-slate-700 to-slate-800 border-slate-700 text-slate-400';
  };

  return (
    <header className="bg-slate-900/95 border-b border-slate-800/80 backdrop-blur-md p-4 sm:p-5 space-y-4 shadow-lg">
      {/* Top row: Branding, Subtitle, Gamified Depth Badge, Stats/Achievements & Reset */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Left: Branding & Tagline */}
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-black tracking-tight bg-gradient-to-r from-white via-slate-100 to-indigo-300 bg-clip-text text-transparent">
              QuestionBot
            </h1>
            <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-[10px] font-semibold uppercase tracking-wider">
              Gemini AI
            </span>
            <span className="px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 text-[10px] font-semibold tracking-wider hidden sm:inline">
              Hackathon Edition
            </span>
          </div>
          <p className="text-xs text-slate-400 flex items-center gap-2">
            <span>An AI that refuses to answer.</span>
            <span className="text-slate-600">•</span>
            <span className="text-amber-400/90 font-medium italic">"THE AI THAT REFUSES TO HELP."</span>
          </p>
        </div>

        {/* Right: Gamified Stats, Depth Experience, and Action Modals */}
        <div className="flex flex-wrap items-center gap-2 sm:gap-3">
          {/* FEATURE 1: QUESTION DEPTH EXPERIENCE */}
          <div className="px-3.5 py-1.5 rounded-xl bg-slate-950 border border-slate-800/80 shadow-md flex items-center gap-3">
            <div className="flex flex-col">
              <span className="text-[9px] font-bold uppercase tracking-wider text-slate-400">
                Question Depth
              </span>
              <span className="text-xs font-extrabold font-mono text-indigo-300">
                {depth} {depth === 1 ? 'LEVEL' : 'LEVELS'} DEEP
              </span>
            </div>
            {/* Progression Title Badge */}
            <span
              className={`px-2 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider border shadow-sm ${getDepthColor()}`}
            >
              {depthTitle}
            </span>
          </div>

          {/* FEATURE 4: ACHIEVEMENTS BUTTON */}
          <button
            onClick={onOpenAchievements}
            className="px-3 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer shadow-sm active:scale-95"
            title="View Hackathon Achievements"
          >
            <span>🏆</span>
            <span className="hidden sm:inline">Awards</span>
            <span className="px-1.5 py-0.2 rounded-full bg-amber-500/20 text-[10px] font-mono font-bold">
              {unlockedAchievementsCount}/{totalAchievementsCount}
            </span>
          </button>

          {/* FEATURE 5: SESSION STATS BUTTON */}
          <button
            onClick={onOpenStats}
            className="px-3 py-1.5 rounded-xl bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer shadow-sm active:scale-95"
            title="View Conversation Stats"
          >
            <span>📊</span>
            <span className="hidden sm:inline">Stats</span>
          </button>

          {/* RESET BUTTON */}
          <button
            onClick={onReset}
            disabled={isResetting}
            className="px-3 py-1.5 rounded-xl bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-400 hover:text-rose-300 text-xs font-semibold flex items-center gap-1.5 transition-all active:scale-95 cursor-pointer disabled:opacity-50"
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

      {/* Middle row: FEATURE 3 — 5 POLISHED PERSONALITY CARDS */}
      <div className="space-y-1.5 pt-1">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
            Select Personality Mode:
          </span>
          {/* FEATURE 2: TRY TO BREAK THE BOT CHALLENGE BUTTON */}
          <button
            onClick={onToggleBreakMode}
            className={`px-3 py-1 rounded-xl text-xs font-bold uppercase tracking-wider transition-all flex items-center gap-1.5 cursor-pointer shadow-md active:scale-95 ${
              isBreakMode
                ? 'bg-rose-600 text-white border border-rose-400 shadow-rose-900/50 animate-pulse'
                : 'bg-slate-950 hover:bg-rose-950/40 text-rose-400 border border-rose-800/60'
            }`}
          >
            <span>{isBreakMode ? '🔥' : '⚔️'}</span>
            <span>{isBreakMode ? 'BREAK MODE ACTIVE' : 'TRY TO BREAK THE BOT'}</span>
          </button>
        </div>

        {/* 5 Personality Cards Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2 pt-1">
          {PERSONALITIES.map((p) => {
            const isSelected = personality === p.id;
            return (
              <button
                key={p.id}
                onClick={() => onSelectPersonality(p.id)}
                className={`p-2.5 rounded-xl text-left border transition-all cursor-pointer flex flex-col justify-between group ${
                  isSelected
                    ? 'bg-indigo-950/60 border-indigo-500/80 shadow-md shadow-indigo-950/50 ring-1 ring-indigo-500/50'
                    : 'bg-slate-950/60 hover:bg-slate-800/60 border-slate-800 text-slate-400 hover:text-slate-200'
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="text-base group-hover:scale-110 transition-transform">
                    {p.emoji}
                  </span>
                  <span
                    className={`text-xs font-bold tracking-tight ${
                      isSelected ? 'text-white' : 'text-slate-300'
                    }`}
                  >
                    {p.name}
                  </span>
                </div>
                <p
                  className={`text-[10px] mt-1 line-clamp-1 leading-tight ${
                    isSelected ? 'text-indigo-200' : 'text-slate-500'
                  }`}
                >
                  {p.desc}
                </p>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
}