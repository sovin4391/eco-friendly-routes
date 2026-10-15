import React from 'react';

export default function StatsModal({ isOpen, onClose, stats = {}, depthTitle = 'UNINITIATED' }) {
  if (!isOpen) return null;

  const questionsAsked = stats.questions_asked ?? 0;
  const questionsReturned = stats.questions_returned ?? 0;
  const answersReceived = stats.answers_received ?? 0;
  const maxDepth = stats.max_depth ?? 0;
  const breakAttempts = stats.break_attempts ?? 0;
  const questionsSurvived = stats.questions_survived ?? 0;
  const depthMessage = stats.depth_message || 'You barely scratched the surface.';
  const personalityUsed = stats.personality_used || 'NORMAL';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div
        className="relative w-full max-w-lg bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl p-6 space-y-5 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Decorative ambient gradient */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <span className="text-2xl">📊</span>
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">Conversation Stats</h2>
              <p className="text-xs text-slate-400">Official QuestionBot Session Results</p>
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

        {/* Humorous Depth Message Callout */}
        <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-950/40 via-purple-950/30 to-slate-950 border border-indigo-500/30 text-center space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-400">
            Depth Verdict ({depthTitle})
          </span>
          <p className="text-sm font-semibold text-slate-200 italic">"{depthMessage}"</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {/* Questions Asked */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-col">
            <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
              Questions Asked
            </span>
            <span className="text-xl font-bold font-mono text-indigo-400 mt-1">
              {questionsAsked}
            </span>
          </div>

          {/* Questions Returned */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-col">
            <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
              Questions Returned
            </span>
            <span className="text-xl font-bold font-mono text-violet-400 mt-1">
              {questionsReturned}
            </span>
          </div>

          {/* ANSWERS RECEIVED - The Central Joke! */}
          <div className="p-3 rounded-xl bg-rose-950/30 border border-rose-500/40 flex flex-col relative overflow-hidden">
            <span className="text-[10px] font-bold uppercase tracking-wider text-rose-300">
              Answers Received
            </span>
            <span className="text-2xl font-black font-mono text-rose-400 mt-0.5 flex items-center gap-1">
              {answersReceived}
              <span className="text-xs font-normal text-rose-300/80 font-sans">(Never!)</span>
            </span>
          </div>

          {/* Max Depth */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-col">
            <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
              Max Depth
            </span>
            <span className="text-xl font-bold font-mono text-cyan-400 mt-1">
              {maxDepth}
            </span>
          </div>

          {/* Break Attempts */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-col">
            <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
              Break Attempts
            </span>
            <span className="text-xl font-bold font-mono text-amber-400 mt-1">
              {breakAttempts}
            </span>
          </div>

          {/* Questions Survived */}
          <div className="p-3 rounded-xl bg-slate-950/70 border border-slate-800 flex flex-col">
            <span className="text-[10px] font-medium uppercase tracking-wider text-slate-400">
              Survived
            </span>
            <span className="text-xl font-bold font-mono text-emerald-400 mt-1">
              {questionsSurvived}
            </span>
          </div>
        </div>

        {/* Mode Used Footer Tag */}
        <div className="text-xs text-slate-400 flex items-center justify-between pt-1">
          <span>
            Active Mode: <strong className="text-slate-200">{personalityUsed}</strong>
          </span>
          <span className="text-[11px] text-slate-500 italic">"The AI that refuses to help."</span>
        </div>

        {/* Footer */}
        <div className="pt-2 border-t border-slate-800 flex justify-end">
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
