import React, { useState, useRef, useEffect } from 'react';
import { Message } from '../hooks/useProject';
import { Send, Bot, User, Sparkles, Wand2 } from 'lucide-react';

interface StoryIntakeChatProps {
  messages: Message[];
  onSendMessage: (text: string) => Promise<void>;
  onTriggerGenerate?: () => void;
  status: string;
  isReadyForGeneration?: boolean;
}

const SAMPLE_PROMPTS = [
  {
    title: 'The Last Lighthouse Keeper',
    text: 'An old lighthouse keeper named Elara discovers the light seals an ancient dark creature beneath the waves. During a catastrophic storm, the light fails, and she has one night to fix it before the creature rises.',
  },
  {
    title: 'The Garden in the Machine',
    text: 'A maintenance robot named Sprocket discovers a single green seedling growing in a server room floor of a metal megacity. Sprocket protects it in secret from cleanup drones sent by the city AI.',
  },
  {
    title: 'The Midnight Bakery',
    text: 'Maya runs a bakery open only from midnight to dawn. A mysterious woman named Vivienne tries to buy the shop to uncover what her family buried beneath the foundation a century ago.',
  },
];

export const StoryIntakeChat: React.FC<StoryIntakeChatProps> = ({
  messages,
  onSendMessage,
  onTriggerGenerate,
  status,
  isReadyForGeneration = false,
}) => {
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSending) return;

    const msg = input.trim();
    setInput('');
    setIsSending(true);
    try {
      await onSendMessage(msg);
    } finally {
      setIsSending(false);
    }
  };

  const handleUseSample = (text: string) => {
    setInput(text);
  };

  return (
    <div className="flex flex-col h-full bg-desk-900 border border-desk-700 rounded-xl overflow-hidden shadow-2xl">
      {/* Chat Header */}
      <div className="px-4 py-3 bg-desk-800 border-b border-desk-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-ink-blue to-purple-500 flex items-center justify-center text-white">
            <Bot className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-paper-100 font-sans">Creative Director Agent</h3>
            <p className="text-[10px] text-paper-300 font-mono">Gemini 3.5 Flash • Collaborative Studio</p>
          </div>
        </div>
        {isReadyForGeneration && (
          <button
            onClick={onTriggerGenerate}
            className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-ink-blue to-indigo-600 hover:from-blue-600 hover:to-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-lg transition-all transform hover:scale-105"
          >
            <Wand2 className="w-3.5 h-3.5" />
            Draw Comic
          </button>
        )}
      </div>

      {/* Message List */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 text-xs">
        {messages.length === 0 ? (
          <div className="space-y-4 py-4">
            <div className="p-3.5 rounded-xl bg-desk-800/80 border border-desk-700 text-paper-200 leading-relaxed">
              <p className="font-semibold text-paper-100 mb-1 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-ink-blue" />
                Welcome to Inkwell Comic Studio
              </p>
              <p>
                Bring me any story idea — messy notes, a synopsis, or a script. I will interview you to lock the creative
                direction, design your character reference sheets, break down panels, and draw the complete comic with
                locked-in character consistency.
              </p>
            </div>

            {/* Quick Sample Prompts */}
            <div className="space-y-2">
              <span className="text-[11px] font-mono text-paper-300 uppercase tracking-wider">Quick Sample Stories:</span>
              <div className="grid grid-cols-1 gap-2">
                {SAMPLE_PROMPTS.map((sp) => (
                  <button
                    key={sp.title}
                    type="button"
                    onClick={() => handleUseSample(sp.text)}
                    className="text-left p-2.5 rounded-lg bg-desk-800/60 border border-desk-700/60 hover:border-ink-blue/60 hover:bg-desk-800 transition-all text-paper-200 group"
                  >
                    <strong className="text-paper-100 text-xs block group-hover:text-ink-blue transition-colors font-display">
                      {sp.title}
                    </strong>
                    <p className="text-[11px] text-paper-300 line-clamp-2 mt-0.5">{sp.text}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={msg.id || i}
              className={`flex items-start gap-2.5 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 text-white ${
                  msg.role === 'user' ? 'bg-ink-blue' : 'bg-desk-700'
                }`}
              >
                {msg.role === 'user' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
              </div>
              <div
                className={`p-3 rounded-2xl max-w-[85%] leading-relaxed whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-ink-blue text-white rounded-tr-xs'
                    : 'bg-desk-800 border border-desk-700 text-paper-100 rounded-tl-xs shadow-md'
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="p-3 bg-desk-800/90 border-t border-desk-700 flex items-center gap-2">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Paste your story or answer the director's questions..."
          rows={2}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          className="flex-1 bg-desk-900 border border-desk-700 rounded-xl px-3 py-2 text-xs text-paper-100 placeholder-paper-300 focus:outline-hidden focus:border-ink-blue resize-none"
        />
        <button
          type="submit"
          disabled={!input.trim() || isSending}
          className="p-2.5 rounded-xl bg-ink-blue text-white disabled:opacity-40 hover:bg-blue-600 transition-colors shadow-md shrink-0"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
