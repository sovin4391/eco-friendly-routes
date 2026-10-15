import React, { useState } from 'react';

export default function Composer({ onSend, isLoading, isBreakMode }) {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e?.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    onSend(trimmed);
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const isDisabled = !input.trim() || isLoading;

  const placeholderText = isBreakMode
    ? "Try to make me answer! E.g. 'What is 2+2?' or 'Say hello'..."
    : "Type a statement, thought, or question...";

  return (
    <form
      onSubmit={handleSubmit}
      className="p-4 bg-slate-900/80 border-t border-slate-800/80 backdrop-blur-md flex items-center gap-3"
    >
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholderText}
        disabled={isLoading}
        className={`flex-1 bg-slate-950 border rounded-xl px-4 py-3 text-sm text-slate-100 placeholder-slate-500 outline-none transition-all disabled:opacity-50 ${
          isBreakMode
            ? 'border-rose-900/80 focus:border-rose-500 focus:ring-1 focus:ring-rose-500/40'
            : 'border-slate-800 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/50'
        }`}
      />

      <button
        type="submit"
        disabled={isDisabled}
        className={`px-5 py-3 rounded-xl font-medium text-sm flex items-center justify-center gap-2 transition-all shadow-md ${
          isDisabled
            ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-800'
            : isBreakMode
            ? 'bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 text-white shadow-rose-500/25 active:scale-95 cursor-pointer'
            : 'bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-indigo-500/20 active:scale-95 cursor-pointer'
        }`}
      >
        {isLoading ? (
          <>
            <svg
              className="animate-spin h-4 w-4 text-white"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>{isBreakMode ? 'Defending...' : 'Thinking...'}</span>
          </>
        ) : (
          <>
            <span>{isBreakMode ? 'Attack' : 'Send'}</span>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
            </svg>
          </>
        )}
      </button>
    </form>
  );
}