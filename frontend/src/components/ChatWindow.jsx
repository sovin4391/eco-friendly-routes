import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';

export default function ChatWindow({ messages, isLoading, onPromptClick }) {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const examplePrompts = [
    "What is the meaning of life?",
    "Why is the sky blue?",
    "How do I become successful?",
    "What is the capital of France?",
  ];

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
      {messages.length === 0 ? (
        <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto py-12 space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 text-3xl font-bold shadow-xl shadow-indigo-500/10">
            ?
          </div>

          <div className="space-y-2">
            <h3 className="text-lg font-bold text-slate-100">
              Welcome to QuestionBot
            </h3>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              The AI with one iron rule: <strong className="text-indigo-300">It never answers.</strong> Whatever you say, it will only interrogate you further.
            </p>
          </div>

          <div className="w-full space-y-2 pt-2">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
              Try an opening thought:
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {examplePrompts.map((prompt, idx) => (
                <button
                  key={idx}
                  onClick={() => onPromptClick && onPromptClick(prompt)}
                  className="text-left text-xs p-3 rounded-xl bg-slate-900/80 hover:bg-slate-850 border border-slate-800 hover:border-indigo-500/40 text-slate-300 transition-all hover:text-white cursor-pointer active:scale-98"
                >
                  "{prompt}"
                </button>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {/* Typing / Thinking Indicator */}
          {isLoading && (
            <div className="flex items-end gap-2.5 my-3 justify-start">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white font-bold text-sm shadow-md shadow-indigo-500/20 shrink-0">
                ?
              </div>
              <div className="px-4 py-3 rounded-2xl bg-slate-900 text-slate-300 border border-slate-800 rounded-bl-xs flex items-center gap-1.5 shadow-lg">
                <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce"></span>
                <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:0.2s]"></span>
                <span className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce [animation-delay:0.4s]"></span>
                <span className="text-xs text-slate-400 ml-2">Framing a question...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      )}
    </div>
  );
}