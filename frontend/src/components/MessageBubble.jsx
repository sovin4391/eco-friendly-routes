import React from 'react';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  const formattedTime = message.timestamp
    ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : '';

  return (
    <div className={`flex items-end gap-2.5 my-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Bot Avatar */}
      {!isUser && (
        <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-indigo-500/20 shrink-0">
          ?
        </div>
      )}

      {/* Bubble Content */}
      <div
        className={`max-w-[80%] sm:max-w-[70%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-lg ${
          isUser
            ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-br-xs'
            : 'bg-slate-900/90 text-slate-100 border border-slate-800/80 rounded-bl-xs'
        }`}
      >
        <div className="flex items-center justify-between gap-4 mb-1">
          <span className="text-[11px] font-semibold tracking-wide uppercase opacity-75">
            {isUser ? 'You' : 'QuestionBot'}
          </span>
          {formattedTime && (
            <span className="text-[10px] opacity-60">
              {formattedTime}
            </span>
          )}
        </div>
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
      </div>

      {/* User Avatar */}
      {isUser && (
        <div className="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700/60 flex items-center justify-center text-slate-300 font-semibold text-xs shrink-0">
          U
        </div>
      )}
    </div>
  );
}