import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import Composer from './components/Composer';

const BACKEND_URL = 'http://127.0.0.1:8000';

export default function App() {
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [questionCount, setQuestionCount] = useState(0);
  const [depth, setDepth] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleSendMessage = async (text) => {
    if (!text.trim() || isLoading) return;

    setErrorMessage(null);

    // Optimistically add user's message to UI for instant feedback
    const optimisticUserMsg = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticUserMsg]);
    setIsLoading(true);

    try {
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: conversationId,
          message: text,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server responded with status ${response.status}`);
      }

      const data = await response.json();
      setConversationId(data.conversation_id);
      setMessages(data.messages);
      setQuestionCount(data.question_count);
      setDepth(data.depth);
    } catch (err) {
      console.error('Chat error:', err);
      setErrorMessage(
        `Failed to reach backend (${err.message}). Is the FastAPI server running on http://127.0.0.1:8000?`
      );
      // Remove optimistic message if server failed
      setMessages((prev) => prev.filter((m) => m.id !== optimisticUserMsg.id));
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = async () => {
    if (isResetting) return;
    setErrorMessage(null);

    if (!conversationId) {
      setMessages([]);
      setQuestionCount(0);
      setDepth(0);
      return;
    }

    setIsResetting(true);
    try {
      const response = await fetch(`${BACKEND_URL}/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ conversation_id: conversationId }),
      });

      if (!response.ok) {
        throw new Error(`Reset failed with status ${response.status}`);
      }

      const data = await response.json();
      setMessages(data.messages || []);
      setQuestionCount(data.question_count || 0);
      setDepth(data.depth || 0);
    } catch (err) {
      console.error('Reset error:', err);
      // Even if server reset fails, clear local view
      setMessages([]);
      setQuestionCount(0);
      setDepth(0);
      setErrorMessage(`Reset warning: ${err.message}`);
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="h-screen w-screen bg-slate-950 text-slate-100 flex flex-col overflow-hidden selection:bg-indigo-500 selection:text-white">
      {/* Decorative ambient background */}
      <div className="fixed inset-0 pointer-events-none flex items-center justify-center">
        <div className="w-[600px] h-[600px] bg-indigo-600/5 blur-[140px] rounded-full"></div>
        <div className="w-[400px] h-[400px] bg-violet-600/5 blur-[120px] rounded-full translate-x-32 -translate-y-20"></div>
      </div>

      <div className="relative z-10 flex-1 flex flex-col h-full max-w-4xl w-full mx-auto sm:my-3 sm:border sm:border-slate-800/80 sm:rounded-2xl bg-slate-950/70 backdrop-blur-xl shadow-2xl overflow-hidden">
        {/* Header & Stats Bar */}
        <Sidebar
          questionCount={questionCount}
          depth={depth}
          onReset={handleReset}
          isResetting={isResetting}
        />

        {/* Error notification banner */}
        {errorMessage && (
          <div className="px-4 py-2.5 bg-rose-500/10 border-b border-rose-500/30 text-rose-300 text-xs flex items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="text-rose-400 font-bold">⚠️</span>
              <span>{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-rose-400 hover:text-white font-bold text-sm px-1 cursor-pointer"
            >
              ✕
            </button>
          </div>
        )}

        {/* Conversation Area */}
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          onPromptClick={handleSendMessage}
        />

        {/* Message Composer */}
        <Composer onSend={handleSendMessage} isLoading={isLoading} />
      </div>
    </div>
  );
}