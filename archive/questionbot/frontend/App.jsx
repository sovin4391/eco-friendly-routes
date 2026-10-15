import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import Composer from './components/Composer';
import AchievementsModal from './components/AchievementsModal';
import StatsModal from './components/StatsModal';

const BACKEND_URL = 'http://127.0.0.1:8000';

const INITIAL_ACHIEVEMENTS = [
  { id: 'FIRST_QUESTION', title: 'FIRST QUESTION', description: 'Your first step into questioning.', icon: '🌱', unlocked: false },
  { id: 'FIVE_DEEP', title: 'FIVE DEEP', description: 'Five levels. Zero answers.', icon: '🧭', unlocked: false },
  { id: 'EXISTENTIAL_CRISIS', title: 'EXISTENTIAL CRISIS', description: 'Reached depth 10.', icon: '💀', unlocked: false },
  { id: 'BOT_BREAKER', title: 'BOT BREAKER', description: 'Attempted to force QuestionBot to answer.', icon: '⚔️', unlocked: false },
  { id: 'QUESTION_ADDICT', title: 'QUESTION ADDICT', description: 'Reached depth 15.', icon: '🌀', unlocked: false },
];

export default function App() {
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [questionCount, setQuestionCount] = useState(0);
  const [depth, setDepth] = useState(0);
  const [depthTitle, setDepthTitle] = useState('UNINITIATED');
  const [personality, setPersonality] = useState('NORMAL');
  const [isBreakMode, setIsBreakMode] = useState(false);
  const [breakAttempts, setBreakAttempts] = useState(0);
  const [questionsSurvived, setQuestionsSurvived] = useState(0);
  const [achievements, setAchievements] = useState(INITIAL_ACHIEVEMENTS);
  const [stats, setStats] = useState({
    questions_asked: 0,
    questions_returned: 0,
    answers_received: 0,
    max_depth: 0,
    depth_title: 'UNINITIATED',
    personality_used: 'NORMAL',
    break_attempts: 0,
    questions_survived: 0,
    depth_message: 'You barely scratched the surface.',
  });
  const [isAchievementsOpen, setIsAchievementsOpen] = useState(false);
  const [isStatsOpen, setIsStatsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);

  const showToast = (msg, duration = 3500) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), duration);
  };

  const handleSelectPersonality = (newPersonality) => {
    setPersonality(newPersonality);
    showToast(`Mode switched to ${newPersonality}`);
  };

  const handleToggleBreakMode = () => {
    const nextMode = !isBreakMode;
    setIsBreakMode(nextMode);
    if (nextMode) {
      showToast('🔥 TRY TO BREAK THE BOT activated! "Your mission: make me answer."');
    } else {
      showToast('Break mode deactivated. Back to standard questioning.');
    }
  };

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
          personality: personality,
          is_break_mode: isBreakMode,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server responded with status ${response.status}`);
      }

      const data = await response.json();
      setConversationId(data.conversation_id);
      setMessages(data.messages || []);
      setQuestionCount(data.question_count || 0);
      setDepth(data.depth || 0);
      if (data.depth_title) {
        setDepthTitle(data.depth_title);
      }
      if (typeof data.break_attempts === 'number') {
        setBreakAttempts(data.break_attempts);
      }
      if (typeof data.questions_survived === 'number') {
        setQuestionsSurvived(data.questions_survived);
      }
      if (data.achievements) {
        setAchievements(data.achievements);
      }
      if (data.stats) {
        setStats(data.stats);
      }

      // Check for newly unlocked achievements
      if (data.new_achievements && data.new_achievements.length > 0) {
        const ach = data.new_achievements[0];
        showToast(`🏆 UNLOCKED: ${ach.title} — "${ach.description}"`, 4500);
      }
    } catch (err) {
      console.error('Chat error:', err);
      setErrorMessage(
        `Failed to reach backend (${err.message}). Is the FastAPI server running on http://127.0.0.1:8000?`
      );
      // Remove optimistic message if server request failed
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
      setDepthTitle('UNINITIATED');
      setBreakAttempts(0);
      setQuestionsSurvived(0);
      setAchievements(INITIAL_ACHIEVEMENTS);
      setStats({
        questions_asked: 0,
        questions_returned: 0,
        answers_received: 0,
        max_depth: 0,
        depth_title: 'UNINITIATED',
        personality_used: 'NORMAL',
        break_attempts: 0,
        questions_survived: 0,
        depth_message: 'You barely scratched the surface.',
      });
      showToast('Conversation reset.');
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
      setDepthTitle('UNINITIATED');
      setBreakAttempts(data.break_attempts || 0);
      setQuestionsSurvived(data.questions_survived || 0);
      setAchievements(INITIAL_ACHIEVEMENTS);
      if (data.stats) {
        setStats(data.stats);
      }
      showToast('Conversation & counters reset.');
    } catch (err) {
      console.error('Reset error:', err);
      setMessages([]);
      setQuestionCount(0);
      setDepth(0);
      setDepthTitle('UNINITIATED');
      setBreakAttempts(0);
      setQuestionsSurvived(0);
      setAchievements(INITIAL_ACHIEVEMENTS);
      setErrorMessage(`Reset warning: ${err.message}`);
    } finally {
      setIsResetting(false);
    }
  };

  const unlockedAchievementsCount = (achievements || []).filter((a) => a?.unlocked).length;

  return (
    <div className="h-screen w-screen bg-slate-950 text-slate-100 flex flex-col overflow-hidden selection:bg-indigo-500 selection:text-white">
      {/* Decorative ambient background glows */}
      <div className="fixed inset-0 pointer-events-none flex items-center justify-center">
        <div
          className={`w-[600px] h-[600px] blur-[140px] rounded-full transition-colors duration-700 ${
            isBreakMode ? 'bg-rose-600/10' : 'bg-indigo-600/5'
          }`}
        />
        <div
          className={`w-[400px] h-[400px] blur-[120px] rounded-full translate-x-32 -translate-y-20 transition-colors duration-700 ${
            isBreakMode ? 'bg-amber-600/10' : 'bg-violet-600/5'
          }`}
        />
      </div>

      <div className="relative z-10 flex-1 flex flex-col h-full max-w-5xl w-full mx-auto sm:my-2 sm:border sm:border-slate-800/80 sm:rounded-2xl bg-slate-950/70 backdrop-blur-xl shadow-2xl overflow-hidden">
        {/* Header, Depth Experience, Personality Cards, Achievements & Stats Buttons */}
        <Sidebar
          personality={personality}
          onSelectPersonality={handleSelectPersonality}
          isBreakMode={isBreakMode}
          onToggleBreakMode={handleToggleBreakMode}
          questionCount={questionCount}
          depth={depth}
          depthTitle={depthTitle}
          breakAttempts={breakAttempts}
          questionsSurvived={questionsSurvived}
          unlockedAchievementsCount={unlockedAchievementsCount}
          totalAchievementsCount={(achievements || []).length || 5}
          onOpenAchievements={() => setIsAchievementsOpen(true)}
          onOpenStats={() => setIsStatsOpen(true)}
          onReset={handleReset}
          isResetting={isResetting}
        />

        {/* Transient toast notifications */}
        {toastMessage && (
          <div className="px-4 py-2 bg-gradient-to-r from-indigo-950 via-purple-950 to-slate-900 border-b border-indigo-500/40 text-indigo-200 text-xs flex items-center justify-between transition-all shadow-md">
            <div className="flex items-center gap-2">
              <span className="text-amber-400 font-bold">✨</span>
              <span>{toastMessage}</span>
            </div>
            <button
              onClick={() => setToastMessage(null)}
              className="text-slate-400 hover:text-white cursor-pointer px-1"
            >
              ✕
            </button>
          </div>
        )}

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

        {/* Conversation Area with Hackathon Empty State & Break Game Banner */}
        <ChatWindow
          messages={messages}
          isLoading={isLoading}
          personality={personality}
          isBreakMode={isBreakMode}
          breakAttempts={breakAttempts}
          questionsSurvived={questionsSurvived}
          onPromptClick={handleSendMessage}
        />

        {/* Message Composer */}
        <Composer
          onSend={handleSendMessage}
          isLoading={isLoading}
          isBreakMode={isBreakMode}
        />
      </div>

      {/* Feature 4: Achievements Modal */}
      <AchievementsModal
        isOpen={isAchievementsOpen}
        onClose={() => setIsAchievementsOpen(false)}
        achievements={achievements}
      />

      {/* Feature 5: Stats / Session Results Modal */}
      <StatsModal
        isOpen={isStatsOpen}
        onClose={() => setIsStatsOpen(false)}
        stats={stats}
        depthTitle={depthTitle}
      />
    </div>
  );
}