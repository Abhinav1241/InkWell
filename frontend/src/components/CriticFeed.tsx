import React, { useEffect, useRef } from 'react';
import { TraceEntry } from '../hooks/useProject';
import {
  ShieldAlert,
  ShieldCheck,
  RefreshCw,
  Terminal,
  Cpu,
  Sparkles,
  Layers,
  ArrowRight,
  Flame,
} from 'lucide-react';

interface CriticFeedProps {
  traces: TraceEntry[];
  currentStatus?: string;
}

export const CriticFeed: React.FC<CriticFeedProps> = ({ traces, currentStatus }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [traces]);

  const getVerdictIcon = (trace: TraceEntry) => {
    const msg = trace.message.toLowerCase();
    if (msg.includes('re-draw') || msg.includes('drift') || msg.includes('rejected') || msg.includes('inconsistency') || trace.level === 'warn') {
      return <ShieldAlert className="w-3.5 h-3.5 text-vermilion-500 shrink-0" />;
    }
    if (msg.includes('✓') || msg.includes('passed') || msg.includes('approved') || trace.level === 'decision') {
      return <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />;
    }
    if (msg.includes('lettering') || msg.includes('typesetting')) {
      return <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0" />;
    }
    return <Cpu className="w-3.5 h-3.5 text-paper-muted shrink-0" />;
  };

  return (
    <div
      className="flex flex-col h-full border border-border-charcoal overflow-hidden shadow-sm"
      style={{
        backgroundColor: 'rgba(26, 24, 21, 0.75)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 border-b border-border-charcoal shrink-0"
        style={{ backgroundColor: 'rgba(20, 18, 16, 0.85)' }}
      >
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-surface-card border border-border-charcoal flex items-center justify-center text-vermilion-500">
            <Terminal className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-paper-cream">
              Live Critic Feed & Reasoning Trace
            </h3>
          </div>
        </div>
        <div className="flex items-center gap-2 text-[10px] font-mono text-paper-muted">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>AUTONOMOUS VISION QA</span>
        </div>
      </div>

      {/* Trace Stream */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3 font-mono text-xs bg-transparent">
        {traces.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-paper-muted p-6 space-y-2">
            <Terminal className="w-6 h-6 text-border-crisp" />
            <p className="text-xs font-sans text-paper-muted max-w-xs">
              Autonomous QA decisions and vision critic evaluations will stream here in real-time.
            </p>
          </div>
        ) : (
          traces.map((trace, i) => {
            const isFailure =
              trace.message.toLowerCase().includes('re-draw') ||
              trace.message.toLowerCase().includes('drift') ||
              trace.message.toLowerCase().includes('rejected') ||
              trace.message.toLowerCase().includes('inconsistency') ||
              trace.level === 'warn';

            const isSuccess =
              trace.message.includes('✓') ||
              trace.message.toLowerCase().includes('passed') ||
              trace.level === 'decision';

            return (
              <div
                key={trace.id || i}
                className={`p-3 border motion-fast animate-fadeIn ${
                  isFailure
                    ? 'bg-ground-950 border-vermilion-500/80 text-paper-cream shadow-sm'
                    : isSuccess
                    ? 'bg-ground-950 border-emerald-500/40 text-paper-cream'
                    : 'bg-ground-950 border-border-charcoal text-paper-muted'
                }`}
              >
                <div className="flex items-start gap-2.5">
                  <div className="mt-0.5">{getVerdictIcon(trace)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <span
                        className={`px-1.5 py-0.2 text-[9px] uppercase font-mono border ${
                          isFailure
                            ? 'bg-vermilion-500/20 text-vermilion-500 border-vermilion-500/50 font-bold'
                            : isSuccess
                            ? 'bg-emerald-950/60 text-emerald-300 border-emerald-700/50'
                            : 'bg-surface-card text-paper-muted border-border-charcoal'
                        }`}
                      >
                        {trace.stage.replace('_', ' ')}
                      </span>

                      <span className="text-[10px] font-mono text-paper-muted/60">
                        {trace.ts ? new Date(trace.ts).toLocaleTimeString() : `T+${i * 2}s`}
                      </span>
                    </div>

                    <p className="font-sans text-xs text-paper-cream leading-relaxed break-words">
                      {trace.message}
                    </p>

                    {trace.data && trace.data.correctedPrompt && (
                      <div className="mt-2 p-2 bg-surface-card border border-border-charcoal text-[11px] text-paper-muted">
                        <strong className="text-vermilion-500 block font-mono text-[9px] uppercase mb-0.5">
                          Auto-Correction Prompt Delta:
                        </strong>
                        <p className="font-mono text-[10px] text-paper-cream">{trace.data.correctedPrompt}</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
        <div ref={bottomRef} />
      </div>

      {/* Footer Status */}
      {currentStatus && (
        <div className="px-4 py-2 bg-ground-950 border-t border-border-charcoal text-[10px] font-mono text-paper-muted flex items-center justify-between shrink-0">
          <span>
            Phase: <strong className="text-paper-cream uppercase">{currentStatus}</strong>
          </span>
          <span className="text-emerald-400 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Active Listening
          </span>
        </div>
      )}
    </div>
  );
};
