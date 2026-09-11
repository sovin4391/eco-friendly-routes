import React from 'react';

export default function AchievementsModal({ isOpen, onClose, achievements = [] }) {
  if (!isOpen) return null;

  const unlockedCount = achievements.filter((a) => a.unlocked).length;
  const totalCount = achievements.length;
  const progressPercent = totalCount > 0 ? Math.round((unlockedCount / totalCount) * 100) : 0;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div
        className="relative w-full max-w-md bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl p-6 space-y-5 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Decorative ambient gradient */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <span className="text-2xl">🏆</span>
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">Hackathon Achievements</h2>
              <p className="text-xs text-slate-400">Unlock awards by getting deep into QuestionBot</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Progress Bar */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-slate-300">Progress</span>
            <span className="text-amber-400 font-mono font-bold">
              {unlockedCount} of {totalCount} Unlocked ({progressPercent}%)
            </span>
          </div>
          <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-amber-500 to-yellow-300 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Achievements List */}
        <div className="space-y-2.5 max-h-[60vh] overflow-y-auto pr-1 scrollbar-thin">
          {achievements.map((ach) => (
            <div
              key={ach.id}
              className={`p-3.5 rounded-xl border transition-all flex items-start gap-3.5 ${
                ach.unlocked
                  ? 'bg-amber-950/20 border-amber-500/40 shadow-sm'
                  : 'bg-slate-950/50 border-slate-800/80 opacity-60'
              }`}
            >
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center text-xl shrink-0 ${
                  ach.unlocked
                    ? 'bg-amber-500/20 border border-amber-500/30'
                    : 'bg-slate-800 border border-slate-700 grayscale'
                }`}
              >
                {ach.unlocked ? ach.icon : '🔒'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h3
                    className={`text-xs font-bold uppercase tracking-wider ${
                      ach.unlocked ? 'text-amber-300' : 'text-slate-400'
                    }`}
                  >
                    {ach.title}
                  </h3>
                  {ach.unlocked ? (
                    <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-[10px] font-bold tracking-wide shrink-0">
                      UNLOCKED
                    </span>
                  ) : (
                    <span className="text-[10px] text-slate-500 font-medium tracking-wide shrink-0">
                      LOCKED
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-300 mt-0.5">{ach.description}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Modal Footer */}
        <div className="pt-2 border-t border-slate-800/80 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
