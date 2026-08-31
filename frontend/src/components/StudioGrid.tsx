import React, { useState } from 'react';
import { Panel, Page, Character } from '../hooks/useProject';
import {
  CheckCircle2,
  RefreshCw,
  AlertTriangle,
  Sparkles,
  Layers,
  User,
  Eye,
  Sliders,
  ShieldAlert,
  ArrowRight,
  Flame,
} from 'lucide-react';

interface StudioGridProps {
  panels: Panel[];
  pages: Page[];
  characters?: Character[];
  progress: number;
  status: string;
  onApprovePanel?: (panelId: string, decision: 'approve' | 'reject', note?: string) => void;
  activeReferencedCharacter?: string | null;
  simulationControls?: React.ReactNode;
}

const PHASES = [
  { id: 'intake', label: 'Intake' },
  { id: 'designing', label: 'Characters' },
  { id: 'planning', label: 'Script Plan' },
  { id: 'drawing', label: 'Panel Art' },
  { id: 'lettering', label: 'Lettering' },
  { id: 'laying_out', label: 'Layout' },
  { id: 'exporting', label: 'Export' },
];

export const StudioGrid: React.FC<StudioGridProps> = ({
  panels,
  pages,
  characters = [],
  progress,
  status,
  onApprovePanel,
  activeReferencedCharacter,
  simulationControls,
}) => {
  // Before / After inspection mode per panel
  const [inspectMode, setInspectMode] = useState<Record<string, 'before' | 'after'>>({});

  const toggleInspect = (panelId: string) => {
    setInspectMode((prev) => ({
      ...prev,
      [panelId]: prev[panelId] === 'before' ? 'after' : 'before',
    }));
  };

  const getPanelStatusBadge = (panel: Panel) => {
    switch (panel.status) {
      case 'approved':
        return (
          <span className="px-2 py-0.5 text-[10px] font-mono bg-emerald-950/80 border border-emerald-500/60 text-emerald-300 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> Approved
          </span>
        );
      case 'generated':
        return (
          <span className="px-2 py-0.5 text-[10px] font-mono bg-surface-base border border-border-crisp text-paper-cream flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-vermilion-500" /> Resolved
          </span>
        );
      case 'needs_review':
      case 'failed':
        return (
          <span className="px-2 py-0.5 text-[10px] font-mono bg-vermilion-500/20 border border-vermilion-500 text-vermilion-500 flex items-center gap-1 font-bold">
            <AlertTriangle className="w-3 h-3" /> Critic Flagged
          </span>
        );
      case 'drafted':
        return (
          <span className="px-2 py-0.5 text-[10px] font-mono bg-surface-card border border-border-charcoal text-paper-muted flex items-center gap-1">
            <RefreshCw className="w-3 h-3 animate-spin text-vermilion-500" /> Drawing...
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 text-[10px] font-mono bg-ground-900 border border-border-charcoal text-paper-muted">
            Pending Gutter
          </span>
        );
    }
  };

  // Expected panel slots: if panels array is smaller than 4, pad with empty gutter frames
  const displayPanels: Panel[] = panels.length > 0 ? panels : Array.from({ length: 4 }).map((_, i) => ({
    id: `gutter_slot_${i}`,
    pageIndex: 0,
    order: i,
    shotType: i === 0 ? 'ESTABLISHING WIDE' : i === 1 ? 'MEDIUM TWO-SHOT' : 'CLOSE-UP',
    staging: 'Center',
    charactersPresent: i === 0 ? ['Elara Thorne'] : [],
    action: 'Awaiting autonomous story breakdown...',
    caption: '',
    dialogue: [],
    draftUri: undefined,
    artUri: undefined,
    letteredUri: undefined,
    status: 'pending' as const,
    criticIterations: 0,
    criticNotes: [],
  }));

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* ── Top Progress Rail ──────────────────────────────────────────────── */}
      <div
        className="border border-border-charcoal p-3.5 shadow-sm shrink-0"
        style={{
          backgroundColor: 'rgba(26, 24, 21, 0.80)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
        }}
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-2 gap-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-sans font-medium uppercase tracking-wider text-paper-cream">
              Studio Pipeline Execution
            </span>
            <span className="text-xs font-mono text-vermilion-500 font-bold">{progress}%</span>
          </div>
          <div className="flex items-center gap-3">
            {simulationControls}
            <span className="text-[10px] font-mono px-2 py-0.5 bg-ground-900 border border-border-charcoal text-paper-cream uppercase">
              Phase: <strong className="text-paper-cream">{status}</strong>
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-ground-950 h-1.5 border border-border-charcoal mb-3 overflow-hidden">
          <div
            className="bg-vermilion-500 h-full motion-fast"
            style={{ width: `${Math.max(5, progress)}%` }}
          />
        </div>

        {/* Phase Badges */}
        <div className="flex items-center justify-between text-[10px] font-mono overflow-x-auto gap-1 pb-0.5">
          {PHASES.map((p, idx) => {
            const currentIdx = PHASES.findIndex((x) => x.id === status);
            const isCompleted = currentIdx > idx || status === 'done';
            const isCurrent = p.id === status;

            return (
              <div
                key={p.id}
                className={`flex items-center gap-1 px-2 py-0.5 border motion-fast ${
                  isCurrent
                    ? 'bg-vermilion-500 text-white font-bold border-vermilion-600 shadow-sm'
                    : isCompleted
                    ? 'bg-surface-elevated border-border-crisp text-paper-cream'
                    : 'bg-ground-900 border-border-charcoal text-paper-muted'
                }`}
              >
                {isCompleted ? (
                  <CheckCircle2 className="w-2.5 h-2.5 text-emerald-400 shrink-0" />
                ) : isCurrent ? (
                  <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse shrink-0" />
                ) : (
                  <span className="w-1.5 h-1.5 rounded-full bg-border-charcoal shrink-0" />
                )}
                <span>{p.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Studio Panels Grid & Memory Sidebar ────────────────────────────── */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 overflow-hidden">
        {/* Main Panel Canvas Area */}
        <div
          className="lg:col-span-9 overflow-y-auto border border-border-charcoal p-4"
          style={{
            backgroundColor: 'rgba(26, 24, 21, 0.80)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
          }}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {displayPanels.map((panel, idx) => {
              const isFailed = panel.status === 'needs_review' || panel.status === 'failed';
              const isResolved = panel.status === 'generated' || panel.status === 'approved';
              const currentInspect = inspectMode[panel.id] || (isFailed ? 'before' : 'after');

              // Determine image src based on inspect toggle
              let activeImageSrc = panel.letteredUri || panel.artUri;
              if (currentInspect === 'before' && panel.draftUri) {
                activeImageSrc = panel.draftUri;
              }

              return (
                <div
                  key={panel.id || idx}
                  className={`bg-ground-950 border overflow-hidden motion-fast flex flex-col group ${
                    isFailed
                      ? 'critic-failed ring-1 ring-vermilion-500/40'
                      : 'border-border-charcoal hover:border-border-crisp'
                  }`}
                >
                  {/* Panel Metadata Header */}
                  <div className="px-3 py-2 bg-ground-950 border-b border-border-charcoal flex items-center justify-between text-xs font-mono">
                    <div className="flex items-center gap-1.5 text-paper-cream">
                      <span className="font-bold text-vermilion-500">#{idx + 1}</span>
                      <span className="text-paper-muted">Page {panel.pageIndex + 1}</span>
                      <span className="px-1.5 py-0.5 bg-surface-card text-[9px] uppercase text-paper-muted border border-border-charcoal">
                        {panel.shotType}
                      </span>
                    </div>
                    <div>{getPanelStatusBadge(panel)}</div>
                  </div>

                  {/* Panel Artwork Canvas with 400ms blur-to-sharp & 600ms crossfade */}
                  <div className="relative aspect-[4/3] bg-ground-900 flex items-center justify-center overflow-hidden">
                    {activeImageSrc ? (
                      <div className="relative w-full h-full">
                        <img
                          src={activeImageSrc}
                          alt={`Panel ${idx + 1}`}
                          className={`w-full h-full object-cover ${
                            panel.criticIterations > 1
                              ? 'animate-crossfade-redraw'
                              : 'animate-blur-resolve'
                          }`}
                        />

                        {/* Pinned Verdict Pin for Critic Failure */}
                        {isFailed && (
                          <div className="absolute top-3 left-3 right-3 verdict-pin p-2.5 text-xs font-sans animate-fadeIn">
                            <div className="flex items-center gap-1.5 text-vermilion-500 font-mono text-[10px] uppercase font-bold mb-1">
                              <ShieldAlert className="w-3.5 h-3.5" />
                              Critic Verdict Pin • Style Drift Detected
                            </div>
                            <p className="text-[11px] text-paper-cream leading-relaxed">
                              {panel.criticNotes && panel.criticNotes.length > 0
                                ? panel.criticNotes[0]
                                : 'Face anatomy & jacket color drifted from Character Reference Sheet. Auto-generating prompt correction...'}
                            </p>
                          </div>
                        )}

                        {/* Before / After Inspection Toggle Button */}
                        {panel.draftUri && (
                          <button
                            onClick={() => toggleInspect(panel.id)}
                            className="absolute bottom-2 right-2 px-2.5 py-1 text-[10px] font-mono uppercase bg-ground-950/90 hover:bg-ground-950 border border-border-crisp text-paper-cream shadow-md flex items-center gap-1 motion-fast"
                          >
                            <Eye className="w-3 h-3 text-vermilion-500" />
                            <span>{currentInspect === 'before' ? 'Show Corrected' : 'Show Rejected Draft'}</span>
                          </button>
                        )}
                      </div>
                    ) : (
                      /* Empty Gutter Frame Placeholder */
                      <div className="flex flex-col items-center justify-center text-center p-6 space-y-2 text-paper-cream bg-ground-900 border border-border-charcoal w-full h-full">
                        <div className="w-10 h-10 border border-paper-muted border-dashed flex items-center justify-center text-paper-cream">
                          #{idx + 1}
                        </div>
                        <span className="text-[11px] font-mono uppercase tracking-wider text-paper-cream">Empty Gutter Frame</span>
                        <span className="text-[10px] font-sans text-paper-muted">
                          Waiting for autonomous layout resolve...
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Panel Action & Dialogue Description */}
                  <div className="p-3 flex-1 flex flex-col justify-between text-xs space-y-2 bg-ground-950 border-t border-border-charcoal font-sans">
                    <p className="text-paper-muted text-[11px] leading-relaxed">
                      <strong className="text-paper-cream font-mono uppercase text-[10px]">Action:</strong> {panel.action}
                    </p>

                    {/* Characters Present */}
                    {panel.charactersPresent && panel.charactersPresent.length > 0 && (
                      <div className="flex items-center gap-1.5 flex-wrap">
                        <span className="text-[9px] font-mono uppercase text-paper-muted">Cast:</span>
                        {panel.charactersPresent.map((c) => (
                          <span
                            key={c}
                            className={`px-1.5 py-0.5 text-[10px] font-mono border ${
                              activeReferencedCharacter === c
                                ? 'bg-vermilion-500 text-white border-vermilion-600 font-bold'
                                : 'bg-surface-card border-border-charcoal text-paper-cream'
                            }`}
                          >
                            👤 {c}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Dialogue Lines */}
                    {panel.dialogue && panel.dialogue.length > 0 && (
                      <div className="p-2 bg-ground-900 border border-border-charcoal space-y-1">
                        {panel.dialogue.map((d, di) => (
                          <p key={di} className="text-[11px] text-paper-cream italic">
                            <span className="not-italic font-mono uppercase text-[10px] text-vermilion-500 font-bold mr-1">
                              {d.speaker || 'Narrator'}:
                            </span>
                            "{d.text}"
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── Memory Reference Sidebar (Character & Style Consistency) ──────── */}
        <div
          className="lg:col-span-3 overflow-y-auto border border-border-charcoal p-4 space-y-4"
          style={{
            backgroundColor: 'rgba(26, 24, 21, 0.80)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
          }}
        >
          <div className="border-b border-border-charcoal pb-3">
            <h3 className="text-xs font-mono uppercase tracking-wider text-vermilion-500 font-bold flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              Memory Reference Cards
            </h3>
            <p className="text-[11px] text-paper-muted font-sans mt-0.5">
              Locked visual bibles consulted by the generator & critic.
            </p>
          </div>

          {/* Character Cards with Memory Pulse on consultation */}
          <div className="space-y-3">
            {characters.length > 0 ? (
              characters.map((char) => {
                const isConsulted = activeReferencedCharacter === char.name;

                return (
                  <div
                    key={char.id}
                    className={`p-3 bg-ground-950 border motion-fast ${
                      isConsulted
                        ? 'memory-pulse-active'
                        : 'border-border-charcoal'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <strong className="text-xs font-display text-paper-cream">{char.name}</strong>
                      <span className="text-[9px] font-mono uppercase text-vermilion-500 px-1 bg-surface-card border border-border-charcoal">
                        {char.role}
                      </span>
                    </div>

                    {/* Reference Sheet Image Thumbnail */}
                    {char.referenceSheetUris && char.referenceSheetUris.length > 0 ? (
                      <div className="aspect-[4/3] bg-ground-900 border border-border-charcoal mb-2 overflow-hidden">
                        <img
                          src={char.referenceSheetUris[0]}
                          alt={char.name}
                          className="w-full h-full object-cover"
                        />
                      </div>
                    ) : (
                      <div className="aspect-[4/3] bg-ground-900 border border-border-charcoal mb-2 flex items-center justify-center text-paper-muted text-[10px] font-mono">
                        Reference Sheet Locked
                      </div>
                    )}

                    <p className="text-[10px] text-paper-muted font-sans leading-relaxed line-clamp-3">
                      {char.description}
                    </p>

                    {isConsulted && (
                      <div className="mt-2 text-[9px] font-mono text-vermilion-500 flex items-center gap-1 animate-pulse">
                        <Flame className="w-3 h-3" />
                        <span>CONSULTING FOR PANEL CONSISTENCY</span>
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="p-3 bg-ground-950 border border-border-charcoal text-paper-muted text-xs">
                No character reference sheets locked yet.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
