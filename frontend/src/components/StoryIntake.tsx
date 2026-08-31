import React, { useState, useRef, useEffect } from 'react';
import { ProjectData, Message } from '../hooks/useProject';
import {
  Send,
  Sparkles,
  Bot,
  User,
  Wand2,
  Palette,
  BookOpen,
  ShieldCheck,
  Layers,
  ArrowRight,
  Loader2,
  CheckCircle2,
} from 'lucide-react';

interface StoryIntakeProps {
  project: ProjectData | null;
  onStartStory: (story: string) => Promise<void>;
  onSendMessage: (text: string) => Promise<void>;
  onTriggerGenerate: () => void;
  isGenerating?: boolean;
  isStarting?: boolean;
}

const SAMPLE_INSPIRATIONS = [
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

const HEADLINE_GLYPHS = [
  { char: 'T', d: 'M24.48 58.72L24.48 15.96L30.24 15.96L30.24 58.72L35.93 60.60L35.93 62L18.80 62L18.80 60.60L24.48 58.72M42.66 16.46L45.98 17.14L8.75 17.14L12.06 16.46L7.20 26.76L5.55 26.43L6.99 11.31L7.64 11.31L12.71 14.34L9.58 13.76L45.15 13.76L42.02 14.34L47.09 11.31L47.74 11.31L49.18 26.43L47.52 26.76' },
  { char: 'e', d: 'M66.59 30.61Q70.08 30.61 72.64 32.16Q75.20 33.70 76.73 36.67Q78.26 39.64 78.62 43.93L56.58 43.93L56.66 41.52L75.16 40.65L72.71 42.16Q72.46 39.57 71.69 37.61Q70.91 35.65 69.54 34.55Q68.18 33.45 66.05 33.45Q63.53 33.45 61.62 34.84Q59.72 36.22 58.65 38.89Q57.59 41.55 57.59 45.40Q57.59 49.40 59.16 52.32Q60.72 55.23 63.53 56.82Q66.34 58.40 70.08 58.40Q71.45 58.40 72.77 58.04Q74.08 57.68 75.38 56.96Q76.67 56.24 77.90 55.20L78.80 56.17Q77 58.40 75.12 59.86Q73.25 61.32 71.16 62.02Q69.08 62.72 66.66 62.72Q62.49 62.72 59.23 60.69Q55.97 58.65 54.10 55.12Q52.23 51.60 52.23 47.10Q52.23 42.56 53.96 38.82Q55.68 35.07 58.91 32.84Q62.13 30.61 66.59 30.61' },
  { char: 'l', d: 'M91.82 16.68L91.82 58.94L97.40 60.67L97.40 62L81.09 62L81.09 60.67L86.56 58.94L86.56 18.15Q86.09 17.58 85.34 17Q84.58 16.42 83.50 15.83Q82.42 15.24 81.02 14.66L81.02 13.94L91.46 10.92L92.18 10.92' },
  { char: 'l', d: 'M109.08 16.68L109.08 58.94L114.66 60.67L114.66 62L98.36 62L98.36 60.67L103.83 58.94L103.83 18.15Q103.36 17.58 102.60 17Q101.85 16.42 100.77 15.83Q99.69 15.24 98.28 14.66L98.28 13.94L108.72 10.92L109.44 10.92' },
  { char: 'm', d: 'M146.12 30.61L147.20 37.20L147.20 58.94L152.42 60.67L152.42 62L136.47 62L136.47 60.67L141.94 58.94L141.94 37.74Q141.36 37.12 140.21 36.55Q139.06 35.97 136.61 35.18L136.61 34.28L145.36 30.61L146.12 30.61M166.49 39.18L166.49 58.94L171.68 60.67L171.68 62L156.02 62L156.02 60.67L161.24 58.94L161.24 41.41Q161.24 39.46 160.39 38.17Q159.54 36.87 158.05 36.22Q156.56 35.58 154.61 35.58Q152.16 35.58 149.88 36.51Q147.59 37.45 146.73 38.89L145.40 37.56Q147.20 35.65 148.78 34.32Q150.36 32.98 151.91 32.17Q153.46 31.36 155.06 30.99Q156.66 30.61 158.46 30.61Q161.38 30.61 163.14 31.87Q164.91 33.13 165.70 35.09Q166.49 37.05 166.49 39.18M185.79 41.30L185.79 58.94L191.33 60.67L191.33 62L175.31 62L175.31 60.67L180.53 58.94L180.53 41.41Q180.53 39.43 179.69 38.15Q178.84 36.87 177.35 36.22Q175.85 35.58 173.91 35.58Q171.46 35.58 169.17 36.51Q166.89 37.45 166.02 38.89L164.69 37.56Q166.49 35.65 168.08 34.32Q169.66 32.98 171.21 32.17Q172.76 31.36 174.36 30.99Q175.96 30.61 177.76 30.61Q182.04 30.61 183.92 33.40Q185.79 36.19 185.79 41.30' },
  { char: 'e', d: 'M207.81 30.61Q211.30 30.61 213.86 32.16Q216.41 33.70 217.94 36.67Q219.47 39.64 219.83 43.93L197.80 43.93L197.87 41.52L216.38 40.65L213.93 42.16Q213.68 39.57 212.90 37.61Q212.13 35.65 210.76 34.55Q209.39 33.45 207.27 33.45Q204.75 33.45 202.84 34.84Q200.93 36.22 199.87 38.89Q198.81 41.55 198.81 45.40Q198.81 49.40 200.37 52.32Q201.94 55.23 204.75 56.82Q207.56 58.40 211.30 58.40Q212.67 58.40 213.98 58.04Q215.30 57.68 216.59 56.96Q217.89 56.24 219.11 55.20L220.01 56.17Q218.21 58.40 216.34 59.86Q214.47 61.32 212.38 62.02Q210.29 62.72 207.88 62.72Q203.70 62.72 200.45 60.69Q197.19 58.65 195.32 55.12Q193.44 51.60 193.44 47.10Q193.44 42.56 195.17 38.82Q196.90 35.07 200.12 32.84Q203.34 30.61 207.81 30.61' },
  { char: 'a', d: 'M263.02 42.45L263.60 44.97Q259.35 45.94 256.65 46.93Q253.95 47.92 252.44 48.97Q250.92 50.01 250.33 51.18Q249.74 52.35 249.74 53.76Q249.74 56.20 251.19 57.50Q252.65 58.80 254.74 58.80Q256.43 58.80 257.84 57.93Q259.24 57.07 260.09 55.66Q260.93 54.26 260.93 52.64L260.93 39.68Q260.93 37.09 259.60 35.54Q258.27 33.99 255.21 33.99Q254.13 33.99 252.72 34.33Q251.32 34.68 249.99 35.36L251.82 33.70Q251.72 34.71 251.52 35.72Q251.32 36.73 251.05 37.52Q250.78 38.31 250.38 38.74Q249.81 39.36 248.94 39.64Q248.08 39.93 247.22 39.93Q246.10 39.93 245.45 39.41Q244.80 38.89 244.80 38.10Q244.80 36.98 245.90 35.74Q247 34.50 248.82 33.40Q250.64 32.30 252.87 31.62Q255.10 30.93 257.40 30.93Q260.54 30.93 262.48 31.89Q264.42 32.84 265.31 34.69Q266.19 36.55 266.19 39.25L266.19 55.70Q266.19 56.82 266.51 57.55Q266.84 58.29 267.47 58.67Q268.10 59.05 269.03 59.05Q269.86 59.05 270.81 58.72Q271.77 58.40 272.67 57.86L272.67 59.52Q271.19 61.14 269.55 61.89Q267.92 62.65 266.51 62.65Q264.78 62.65 263.54 61.87Q262.30 61.10 261.65 59.64Q261 58.18 261 56.20L261.22 55.84Q260.75 57.86 259.47 59.41Q258.20 60.96 256.41 61.84Q254.63 62.72 252.62 62.72Q249.02 62.72 246.68 60.70Q244.34 58.69 244.34 54.91Q244.34 52.89 245.15 51.24Q245.96 49.58 248.01 48.12Q250.06 46.66 253.71 45.28Q257.37 43.89 263.02 42.45' },
  { char: 's', d: 'M305.13 30.61Q307.14 30.61 308.80 31Q310.46 31.40 312.54 32.44L313.08 40.94L311.54 40.94L308.01 32.19L310.46 35.22Q309.12 34.17 307.92 33.65Q306.71 33.13 305.24 33.13Q302.54 33.13 300.97 34.32Q299.40 35.50 299.40 37.63Q299.40 39.39 300.38 40.51Q301.35 41.62 302.93 42.43Q304.52 43.24 306.32 44.07Q307.68 44.68 309.02 45.46Q310.35 46.23 311.43 47.31Q312.51 48.39 313.17 49.90Q313.84 51.42 313.84 53.54Q313.84 56.49 312.38 58.54Q310.92 60.60 308.42 61.66Q305.92 62.72 302.72 62.72Q300.63 62.72 298.99 62.41Q297.35 62.11 295.73 61.42L294.11 52.75L295.80 52.75L300.63 61.71L296.24 58.90Q297.60 59.55 298.52 59.88Q299.44 60.20 300.20 60.29Q300.95 60.38 301.74 60.38Q305.16 60.38 307.16 59.01Q309.16 57.64 309.16 54.94Q309.16 53.43 308.46 52.42Q307.76 51.42 306.59 50.68Q305.42 49.94 304.05 49.33Q302.68 48.72 301.38 48.07Q299.66 47.17 298.22 46.05Q296.78 44.94 295.91 43.24Q295.05 41.55 295.05 39.03Q295.05 36.37 296.36 34.50Q297.68 32.62 299.96 31.62Q302.25 30.61 305.13 30.61' },
  { char: 't', d: 'M326.68 32.41L326.68 53.36Q326.68 55.77 328.14 56.98Q329.60 58.18 332.30 58.18Q333.56 58.18 335.03 57.93Q336.51 57.68 338.24 57.18L338.24 58.87Q336.15 60.34 334.58 61.15Q333.02 61.96 331.76 62.27Q330.50 62.58 329.27 62.58Q326.90 62.58 325.13 61.69Q323.37 60.81 322.40 59.07Q321.42 57.32 321.42 54.76L321.42 36.19L317.54 33.49L317.54 32.84Q318.33 32.26 319.10 31.67Q319.88 31.08 320.67 30.46Q321.46 29.85 322.25 29.22Q323.04 28.59 323.87 27.94Q324.70 27.30 325.56 26.61L326.68 26.61L326.68 32.41M336.62 34.64L324.63 34.64L324.63 31.33L337.19 31.33' },
  { char: 'o', d: 'M355.90 59.95Q358.60 59.95 360.72 58.63Q362.85 57.32 364.07 54.57Q365.30 51.81 365.30 47.53Q365.30 42.92 364.09 39.77Q362.88 36.62 360.72 35Q358.56 33.38 355.65 33.38Q352.95 33.38 350.82 34.69Q348.70 36.01 347.48 38.76Q346.25 41.52 346.25 45.80Q346.25 50.37 347.46 53.54Q348.66 56.71 350.84 58.33Q353.02 59.95 355.90 59.95M355.68 62.72Q351.15 62.72 347.67 60.72Q344.20 58.72 342.26 55.18Q340.31 51.63 340.31 47.02Q340.31 42.27 342.35 38.56Q344.38 34.86 347.89 32.73Q351.40 30.61 355.86 30.61Q360.44 30.61 363.89 32.61Q367.35 34.60 369.29 38.13Q371.24 41.66 371.24 46.30Q371.24 51.06 369.20 54.76Q367.17 58.47 363.66 60.60Q360.15 62.72 355.68 62.72' },
  { char: 'r', d: 'M395.70 30.86Q397.54 30.86 398.37 31.72Q399.20 32.59 399.20 33.99Q399.20 35.61 398.15 36.60Q397.11 37.59 395.27 37.59Q394.48 37.59 393.69 37.29Q392.90 36.98 392.01 36.69Q391.13 36.40 390.09 36.40Q389.26 36.40 388.25 36.64Q387.24 36.87 386.27 37.30Q385.30 37.74 384.58 38.31L383.79 37.05Q385.91 35.47 387.69 34.32Q389.48 33.16 390.95 32.39Q392.43 31.62 393.62 31.24Q394.80 30.86 395.70 30.86M384.90 30.61L385.26 37.20L385.26 58.94L390.84 60.67L390.84 62L374.54 62L374.54 60.67L380.01 58.94L380.01 37.74Q379.54 37.23 378.80 36.84Q378.06 36.44 377.04 36.03Q376.01 35.61 374.68 35.18L374.68 34.28L384.15 30.61' },
  { char: 'y', d: 'M409.16 34.39L419.38 56.71L416.64 63.33L403.50 34.57L399.04 32.88L399.04 31.33L413.84 31.33L413.84 32.88L409.16 34.39M406.64 81.08Q404.80 81.08 403.58 80.05Q402.35 79.03 402.35 77.26Q402.35 76.33 402.73 75.63Q403.11 74.92 403.76 74.51Q404.40 74.10 405.12 74.10Q405.88 74.10 406.47 74.42Q407.07 74.74 407.72 75.07Q408.36 75.39 409.16 75.39Q409.91 75.39 410.56 75.07Q411.21 74.74 411.82 73.90Q412.43 73.05 413.04 71.50L417.26 60.78L418.98 56.13L427.05 34.21L422.33 32.88L422.33 31.33L433.96 31.33L433.96 32.88L430.18 34.21L416.50 69.92Q414.84 74.24 413.33 76.67Q411.82 79.10 410.20 80.09Q408.58 81.08 406.64 81.08' },
  { char: '.', d: 'M441.36 53.94Q443.27 53.94 444.50 55.18Q445.72 56.42 445.72 58.22Q445.72 59.98 444.50 61.24Q443.27 62.50 441.36 62.50Q439.49 62.50 438.25 61.24Q437.01 59.98 437.01 58.22Q437.01 56.42 438.25 55.18Q439.49 53.94 441.36 53.94' },
];

export const StoryIntake: React.FC<StoryIntakeProps> = ({
  project,
  onStartStory,
  onSendMessage,
  onTriggerGenerate,
  isGenerating = false,
  isStarting = false,
}) => {
  const [initialPrompt, setInitialPrompt] = useState('');
  const [chatInput, setChatInput] = useState('');
  const [isSubmittingTurn, setIsSubmittingTurn] = useState(false);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  // One-time ink-draw entrance animation state
  const [introDone, setIntroDone] = useState<boolean>(() => {
    if (typeof window === 'undefined') return true;
    try {
      // Dev-only escape hatch: check ?replayIntro=1 query param
      const urlParams = new URLSearchParams(window.location.search);
      const isReplayRequested = urlParams.has('replayIntro');
      if (isReplayRequested) {
        sessionStorage.removeItem('inkwell_intro_played');
        return false;
      }
      return sessionStorage.getItem('inkwell_intro_played') === 'true';
    } catch {
      return false;
    }
  });

  const [animPhase, setAnimPhase] = useState<'drawing' | 'revealed'>(() => {
    if (typeof window === 'undefined') return 'revealed';
    try {
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.has('replayIntro')) return 'drawing';
      return sessionStorage.getItem('inkwell_intro_played') === 'true' ? 'revealed' : 'drawing';
    } catch {
      return 'revealed';
    }
  });

  // Expose window.replayIntro() in dev environments
  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).replayIntro = () => {
        sessionStorage.removeItem('inkwell_intro_played');
        window.location.reload();
      };
    }
  }, []);

  useEffect(() => {
    if (introDone) return;

    const prefersReduced =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    const isReplayRequested =
      typeof window !== 'undefined' &&
      new URLSearchParams(window.location.search).has('replayIntro');

    if (prefersReduced) {
      setAnimPhase('revealed');
      setIntroDone(true);
      try {
        if (!isReplayRequested) {
          sessionStorage.setItem('inkwell_intro_played', 'true');
        }
      } catch {}
      return;
    }

    // After headline finishes drawing (t ≈ 1.25s), begin staggered arrival flow
    const revealTimer = setTimeout(() => {
      setAnimPhase('revealed');
    }, 1250);

    // End of full sequence (headline 1.25s + stagger + 550ms ease = ~2.15s)
    const doneTimer = setTimeout(() => {
      setIntroDone(true);
      try {
        if (!isReplayRequested) {
          sessionStorage.setItem('inkwell_intro_played', 'true');
        }
      } catch {}
    }, 2200);

    return () => {
      clearTimeout(revealTimer);
      clearTimeout(doneTimer);
    };
  }, [introDone]);

  // Auto-scroll chat to bottom on new messages
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [project?.messages]);

  const handleStartSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!initialPrompt.trim() || isStarting) return;
    await onStartStory(initialPrompt.trim());
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || isSubmittingTurn) return;
    const msg = chatInput.trim();
    setChatInput('');
    setIsSubmittingTurn(true);
    try {
      await onSendMessage(msg);
    } finally {
      setIsSubmittingTurn(false);
    }
  };

  // Detect OS for shortcut guidance
  const isMac =
    typeof window !== 'undefined' &&
    (/Mac|iPod|iPhone|iPad/.test(navigator.platform || '') || /Mac/.test(navigator.userAgent || ''));
  const shortcutHint = isMac ? 'Cmd+Enter to begin' : 'Ctrl+Enter to begin';

  const wordCount = initialPrompt.trim() ? initialPrompt.trim().split(/\s+/).length : 0;
  const lengthCalibration =
    wordCount === 0
      ? shortcutHint
      : wordCount < 25
      ? `${wordCount} words · great for a quick 2-page sketch`
      : wordCount <= 120
      ? `${wordCount} words · ideal for a tight 4-page arc`
      : `${wordCount} words · rich foundation for full comic`;

  // ── 1. EMPTY FIRST SCREEN (Pristine Minimalist Slate) ──────────────────────
  if (!project) {
    return (
      <div className="relative h-full flex flex-col items-center justify-center p-6 max-w-5xl mx-auto">
        <div className="relative z-10 w-full space-y-7 animate-fadeIn">
          {/* Headline & Invitation Line */}
          <div className="text-center space-y-3">
            {introDone ? (
              <h1 className="text-4xl md:text-6xl lg:text-[7rem] font-display font-medium text-paper-cream tracking-tight">
                Tell me a story.
              </h1>
            ) : (
              <div className="flex justify-center items-center h-[48px] sm:h-[64px] md:h-[80px] lg:h-[112px]" aria-label="Tell me a story.">
                <svg
                  viewBox="0 0 459 85"
                  className="w-full max-w-[360px] sm:max-w-[480px] md:max-w-[640px] lg:max-w-[840px] h-auto overflow-visible"
                  aria-hidden="true"
                >
                  {HEADLINE_GLYPHS.map((glyph, index) => (
                    <path
                      key={index}
                      d={glyph.d}
                      className="animate-ink-glyph"
                      style={{
                        animationDelay: `${index * 40}ms`,
                      }}
                    />
                  ))}
                </svg>
                <h1 className="sr-only">Tell me a story.</h1>
              </div>
            )}

            {/* 1. Subhead: arrives first (delay 0ms) */}
            <p
              className="text-base md:text-xl text-paper-cream font-medium max-w-2xl mx-auto font-sans leading-relaxed"
              style={{
                textShadow: '0 1px 3px rgba(0,0,0,0.6)',
                ...(introDone
                  ? {}
                  : {
                      opacity: animPhase === 'revealed' ? 1 : 0,
                      transform: animPhase === 'revealed' ? 'translateY(0px)' : 'translateY(12px)',
                      transition: 'opacity 550ms cubic-bezier(0.16, 1, 0.3, 1), transform 550ms cubic-bezier(0.16, 1, 0.3, 1)',
                      transitionDelay: '0ms',
                    })
              }}
            >
              Paste rough notes, a scene premise, or a full script. The Creative Director will lock the story bible,
              design character sheets, and coordinate the comic pipeline.
            </p>
          </div>

          {/* Minimalist Large Story Input Form */}
          <form onSubmit={handleStartSubmit} className="space-y-4">
            {/* 2. Comic Panel: arrives second (delay 100ms) */}
            <div
              className="relative group"
              style={
                introDone
                  ? undefined
                  : {
                      opacity: animPhase === 'revealed' ? 1 : 0,
                      transform: animPhase === 'revealed' ? 'translateY(0px)' : 'translateY(12px)',
                      transition: 'opacity 550ms cubic-bezier(0.16, 1, 0.3, 1), transform 550ms cubic-bezier(0.16, 1, 0.3, 1)',
                      transitionDelay: '100ms',
                    }
              }
            >
              <textarea
                value={initialPrompt}
                onChange={(e) => setInitialPrompt(e.target.value)}
                placeholder="Once upon a time in a rain-drenched coastal town, an old keeper noticed the beacon flicker..."
                disabled={isStarting}
                style={{ boxShadow: '0 0 60px rgba(139, 58, 32, 0.15)' }}
                className="w-full min-h-[240px] bg-surface-card border border-border-charcoal focus:border-vermilion-500 p-6 text-base md:text-lg text-paper-cream placeholder:text-paper-muted/50 focus:outline-none resize-none motion-fast leading-relaxed"
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                    e.preventDefault();
                    handleStartSubmit(e);
                  }
                }}
              />
              <div className="absolute right-4 bottom-4 text-[10px] font-mono text-paper-muted bg-surface-card/90 px-2 py-0.5 border border-border-charcoal pointer-events-none select-none">
                {lengthCalibration}
              </div>
            </div>

            {/* 3. Sample Prompts: arrives third (delay 200ms) */}
            <div
              className="space-y-2 pt-1"
              style={
                introDone
                  ? undefined
                  : {
                      opacity: animPhase === 'revealed' ? 1 : 0,
                      transform: animPhase === 'revealed' ? 'translateY(0px)' : 'translateY(12px)',
                      transition: 'opacity 550ms cubic-bezier(0.16, 1, 0.3, 1), transform 550ms cubic-bezier(0.16, 1, 0.3, 1)',
                      transitionDelay: '200ms',
                    }
              }
            >
              <div className="flex items-center justify-between text-[11px] font-mono uppercase tracking-wider text-paper-muted">
                <span>Or select a sample premise:</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
                {SAMPLE_INSPIRATIONS.map((sample) => (
                  <button
                    key={sample.title}
                    type="button"
                    onClick={() => setInitialPrompt(sample.text)}
                    disabled={isStarting}
                    style={{
                      backgroundColor: 'rgba(26, 24, 21, 0.75)',
                      backdropFilter: 'blur(12px)',
                      WebkitBackdropFilter: 'blur(12px)',
                    }}
                    className="p-4 text-left hover:bg-surface-hover/90 hover:border-border-crisp border border-border-charcoal motion-fast group focus:outline-none focus:ring-1 focus:ring-vermilion-500"
                  >
                    <div className="font-display font-semibold text-sm text-paper-cream group-hover:text-vermilion-500 motion-fast truncate" style={{ textShadow: '0 1px 2px rgba(0,0,0,0.5)' }}>
                      {sample.title}
                    </div>
                    <p className="text-xs text-paper-muted font-sans line-clamp-2 mt-1.5 leading-relaxed">
                      {sample.text}
                    </p>
                  </button>
                ))}
              </div>
            </div>

            {/* 4. Primary Action Button: arrives fourth (delay 300ms) */}
            <div
              className="pt-3 flex justify-center"
              style={
                introDone
                  ? undefined
                  : {
                      opacity: animPhase === 'revealed' ? 1 : 0,
                      transform: animPhase === 'revealed' ? 'translateY(0px)' : 'translateY(12px)',
                      transition: 'opacity 550ms cubic-bezier(0.16, 1, 0.3, 1), transform 550ms cubic-bezier(0.16, 1, 0.3, 1)',
                      transitionDelay: '300ms',
                    }
              }
            >
              <button
                type="submit"
                disabled={!initialPrompt.trim() || isStarting}
                className="w-full sm:w-auto min-w-[260px] px-8 py-3.5 bg-vermilion-500 hover:bg-vermilion-600 disabled:opacity-40 disabled:cursor-not-allowed disabled:pointer-events-none text-white font-sans text-xs font-semibold tracking-widest uppercase flex items-center justify-center gap-2 motion-fast shadow-vermilion-glow"
              >
                {isStarting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Analyzing Premise...</span>
                  </>
                ) : (
                  <>
                    <span>Begin Drafting Story</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  // ── 2. ACTIVE STORY & INTAKE CONVERSATION (Once project exists) ─────────────
  const options = project.options || {
    style: 'manga-influenced modern comic',
    pageCount: 6,
    rating: 'all-ages',
    aspect: '3:4',
    palette: 'vibrant',
    pacing: 'balanced',
  };

  const messages: Message[] = project.messages || [];
  const isReadyForGen =
    project.status === 'designing' ||
    project.status === 'planning' ||
    Boolean(project.characters && project.characters.length > 0) ||
    Boolean(project.logline);

  return (
    <div className="h-full grid grid-cols-1 lg:grid-cols-12 gap-5 overflow-hidden animate-fadeIn">
      {/* ── Left Column: Ongoing Conversation with Creative Director ─────── */}
      <div className="lg:col-span-7 flex flex-col h-full bg-surface-card border border-border-charcoal overflow-hidden">
        {/* Chat Masthead */}
        <div className="px-5 py-3.5 bg-ground-950 border-b border-border-charcoal flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 bg-vermilion-500 flex items-center justify-center text-white text-xs font-serif shadow-sm">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-display font-medium text-paper-cream">Creative Director Agent</h2>
              <p className="text-[10px] font-mono text-paper-muted">Gemini 2.5 Flash • Story Bible Extraction</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 text-[10px] font-mono uppercase bg-surface-base border border-border-charcoal text-paper-muted">
              {project.status.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Conversation Stream */}
        <div ref={chatScrollRef} className="flex-1 p-5 overflow-y-auto space-y-4 text-xs font-sans">
          {messages.length === 0 ? (
            <div className="p-4 bg-surface-base border border-border-charcoal text-paper-muted space-y-2 leading-relaxed">
              <div className="flex items-center gap-2 text-paper-cream font-medium">
                <Sparkles className="w-3.5 h-3.5 text-vermilion-500" />
                <span>Story Intake in Progress</span>
              </div>
              <p>
                The Creative Director is reviewing your premise. Respond to any questions below to lock in the
                character descriptions, visual tone, and page layout.
              </p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={msg.id || idx}
                className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {msg.role !== 'user' && (
                  <div className="w-6 h-6 bg-ground-950 border border-border-charcoal flex items-center justify-center text-vermilion-500 shrink-0 mt-0.5">
                    <Bot className="w-3.5 h-3.5" />
                  </div>
                )}

                <div
                  className={`p-4 max-w-[85%] leading-relaxed whitespace-pre-wrap ${
                    msg.role === 'user'
                      ? 'bg-surface-elevated border border-border-prominent text-paper-cream shadow-sm'
                      : 'bg-ground-950 border border-border-charcoal text-paper-cream font-sans shadow-inner'
                  }`}
                >
                  {msg.role !== 'user' && (
                    <div className="text-[10px] font-mono uppercase text-paper-muted mb-1 flex items-center gap-1.5">
                      <span className="w-1.5 h-1.5 rounded-full bg-vermilion-500" />
                      Creative Director
                    </div>
                  )}
                  <p className="text-xs md:text-sm leading-relaxed">{msg.text}</p>
                </div>

                {msg.role === 'user' && (
                  <div className="w-6 h-6 bg-surface-elevated border border-border-crisp flex items-center justify-center text-paper-cream shrink-0 mt-0.5">
                    <User className="w-3.5 h-3.5" />
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {/* Interactive Chat Turn Input */}
        <form onSubmit={handleChatSubmit} className="p-3 bg-ground-950 border-t border-border-charcoal flex items-center gap-2 shrink-0">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder="Reply to the director or provide additional details..."
            disabled={isSubmittingTurn}
            className="flex-1 bg-surface-card border border-border-charcoal focus:border-vermilion-500 px-4 py-2.5 text-xs text-paper-cream placeholder:text-paper-muted/50 focus:outline-none motion-fast"
          />
          <button
            type="submit"
            disabled={!chatInput.trim() || isSubmittingTurn}
            className="px-4 py-2.5 bg-vermilion-500 hover:bg-vermilion-600 border border-vermilion-500 disabled:opacity-40 disabled:cursor-not-allowed disabled:pointer-events-none text-white text-xs font-medium flex items-center gap-1.5 motion-fast shrink-0 shadow-sm"
          >
            {isSubmittingTurn ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Send className="w-3.5 h-3.5" />
            )}
            <span className="hidden sm:inline">Send</span>
          </button>
        </form>
      </div>

      {/* ── Right Column: Story Bible & Direction Summary ─────────────────── */}
      <div className="lg:col-span-5 flex flex-col gap-4 overflow-y-auto">
        {/* Story Bible Summary Card */}
        <div className="bg-surface-card border border-border-charcoal p-5 space-y-4">
          <div className="border-b border-border-charcoal pb-3">
            <h3 className="text-sm font-display font-medium text-paper-cream tracking-tight">
              Story Bible & Direction Summary
            </h3>
            <p className="text-xs text-paper-muted font-sans mt-0.5">
              Locked visual parameters extracted from your story.
            </p>
          </div>

          {/* Premise & Logline */}
          <div className="bg-ground-950 p-4 border border-border-charcoal space-y-1">
            <span className="text-[10px] font-mono uppercase text-vermilion-500 font-bold block">
              Story Premise & Logline
            </span>
            <p className="text-sm text-paper-cream font-display italic leading-relaxed">
              "{project.logline || project.title || 'Extracting premise from intake conversation...'}"
            </p>
          </div>

          {/* Direction Metadata Grid */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="bg-ground-950 p-3 border border-border-charcoal space-y-1">
              <span className="flex items-center gap-1.5 text-paper-muted text-[10px] font-mono uppercase">
                <Palette className="w-3 h-3 text-vermilion-500" />
                Art Style
              </span>
              <strong className="text-paper-cream block capitalize font-sans">{options.style}</strong>
            </div>

            <div className="bg-ground-950 p-3 border border-border-charcoal space-y-1">
              <span className="flex items-center gap-1.5 text-paper-muted text-[10px] font-mono uppercase">
                <BookOpen className="w-3 h-3 text-paper-cream" />
                Target Pages
              </span>
              <strong className="text-paper-cream block font-sans">{options.pageCount} Pages</strong>
            </div>

            <div className="bg-ground-950 p-3 border border-border-charcoal space-y-1">
              <span className="flex items-center gap-1.5 text-paper-muted text-[10px] font-mono uppercase">
                <ShieldCheck className="w-3 h-3 text-emerald-400" />
                Content Rating
              </span>
              <strong className="text-paper-cream block uppercase font-mono">{options.rating}</strong>
            </div>

            <div className="bg-ground-950 p-3 border border-border-charcoal space-y-1">
              <span className="flex items-center gap-1.5 text-paper-muted text-[10px] font-mono uppercase">
                <Layers className="w-3 h-3 text-amber-400" />
                Color Palette
              </span>
              <strong className="text-paper-cream block capitalize font-sans">{options.palette}</strong>
            </div>
          </div>

          {/* Character Keyframes Detected */}
          {project.characters && project.characters.length > 0 && (
            <div className="space-y-2 pt-2 border-t border-border-charcoal">
              <span className="text-[10px] font-mono uppercase text-paper-muted block">
                Identified Characters ({project.characters.length})
              </span>
              <div className="space-y-2">
                {project.characters.map((char) => (
                  <div key={char.id} className="p-2.5 bg-ground-950 border border-border-charcoal flex items-start gap-2.5">
                    <div className="w-5 h-5 bg-surface-elevated flex items-center justify-center text-[10px] font-serif text-paper-cream shrink-0 mt-0.5">
                      {char.name[0]}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between">
                        <strong className="text-xs text-paper-cream font-medium truncate">{char.name}</strong>
                        <span className="text-[10px] font-mono text-paper-muted uppercase">{char.role}</span>
                      </div>
                      <p className="text-[11px] text-paper-muted line-clamp-2 mt-0.5">{char.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Primary Action Button */}
          <div className="pt-2">
            <button
              onClick={onTriggerGenerate}
              disabled={isGenerating}
              className="w-full py-3.5 bg-vermilion-500 hover:bg-vermilion-600 disabled:bg-vermilion-500/60 disabled:cursor-not-allowed disabled:pointer-events-none text-white text-xs font-sans font-semibold uppercase tracking-wider flex items-center justify-center gap-2 motion-fast shadow-vermilion-glow"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Generating Pipeline...</span>
                </>
              ) : (
                <>
                  <Wand2 className="w-4 h-4" />
                  <span>Generate Comic Studio Pipeline</span>
                </>
              )}
            </button>
            <p className="text-[10px] text-paper-muted text-center mt-2 font-mono">
              Starts character design, panel breakdown, drawing, and vision critique.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
