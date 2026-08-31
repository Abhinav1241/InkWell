import React, { useState } from 'react';
import {
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Play,
  RotateCcw,
  Layers,
  Palette,
  Type,
  Maximize2,
  Clock,
  Sliders,
  Eye,
  ArrowRight,
} from 'lucide-react';

export function StyleGuide() {
  // Interactive motion state demo
  const [panelResolved, setPanelResolved] = useState(false);
  const [isResolving, setIsResolving] = useState(false);

  // Critic redraw crossfade demo
  const [criticState, setCriticState] = useState<'idle' | 'failed' | 'redrawing' | 'corrected'>('idle');

  const triggerPanelResolve = () => {
    setPanelResolved(false);
    setIsResolving(true);
    setTimeout(() => {
      setPanelResolved(true);
      setIsResolving(false);
    }, 400);
  };

  const triggerCriticDemo = () => {
    setCriticState('failed');
    setTimeout(() => {
      setCriticState('redrawing');
      setTimeout(() => {
        setCriticState('corrected');
      }, 600);
    }, 1500);
  };

  const resetCriticDemo = () => {
    setCriticState('idle');
  };

  return (
    <div className="min-h-screen bg-ground-900 text-paper-cream p-6 md:p-12 overflow-y-auto selection:bg-vermilion-500 selection:text-white">
      {/* ── Header / Editorial Masthead ───────────────────────────────────── */}
      <header className="max-w-6xl mx-auto border-b border-border-charcoal pb-8 mb-12">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-vermilion-500 text-xs font-mono tracking-widest uppercase mb-2">
              <span className="w-2 h-2 rounded-full bg-vermilion-500 animate-pulse" />
              Inkwell Design System Foundation — Chunk 1
            </div>
            <h1 className="text-4xl md:text-5xl font-display font-medium text-paper-cream tracking-tight">
              Editorial Print, Rendered Dark
            </h1>
            <p className="text-paper-muted text-sm md:text-base mt-2 max-w-2xl font-sans leading-relaxed">
              A designer’s studio and a printed page. Hard panel edges as the interface language, warm charcoal grounds,
              paper-cream on dark contrast, and a single vermilion accent (<code className="text-vermilion-500 font-mono">#EA5A2C</code>).
            </p>
          </div>
          <div className="flex items-center gap-3 font-mono text-xs text-paper-muted bg-surface-card px-4 py-2 rounded-none border border-border-charcoal">
            <span>VERSION 1.0.0</span>
            <span>•</span>
            <span className="text-paper-cream">CHUNK 1 DELIVERABLE</span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto space-y-16">
        {/* ── 1. Color Palette Tokens ──────────────────────────────────────── */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 border-b border-border-charcoal pb-3">
            <Palette className="w-4 h-4 text-vermilion-500" />
            <h2 className="text-xl font-display font-semibold tracking-tight text-paper-cream">
              1. Color Palette & Ground Tokens
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Ground (Warm Charcoal) */}
            <div className="bg-surface-card border border-border-charcoal p-5 space-y-4">
              <div className="text-xs font-mono uppercase text-paper-muted">Ground (#1A1815 Family)</div>
              <div className="space-y-2">
                <div className="h-14 bg-ground-950 border border-border-charcoal flex items-end p-2 text-[11px] font-mono text-paper-muted">
                  ground-950 #12110F (Deepest)
                </div>
                <div className="h-14 bg-ground-900 border border-border-crisp flex items-end p-2 text-[11px] font-mono text-paper-cream">
                  ground-900 #1A1815 (Workspace Base)
                </div>
                <div className="h-14 bg-ground-850 border border-border-charcoal flex items-end p-2 text-[11px] font-mono text-paper-cream">
                  ground-850 #22201C (Elevated)
                </div>
              </div>
              <p className="text-xs text-paper-muted font-sans leading-normal">
                Warm charcoal ground — never pure pitch black, never sterile cool blue-grey.
              </p>
            </div>

            {/* Surfaces & 1px Hard Borders */}
            <div className="bg-surface-card border border-border-charcoal p-5 space-y-4">
              <div className="text-xs font-mono uppercase text-paper-muted">Surfaces & Hard Edges</div>
              <div className="space-y-2">
                <div className="h-14 bg-surface-card border border-border-charcoal flex items-end p-2 text-[11px] font-mono text-paper-cream">
                  surface-card #2A2722 (1px Border)
                </div>
                <div className="h-14 bg-surface-hover border border-border-crisp flex items-end p-2 text-[11px] font-mono text-paper-cream">
                  surface-hover #33302A
                </div>
                <div className="h-14 bg-surface-active border border-border-prominent flex items-end p-2 text-[11px] font-mono text-paper-cream">
                  surface-active #3E3A33
                </div>
              </div>
              <p className="text-xs text-paper-muted font-sans leading-normal">
                Crisp 1px borders defined by hard comic panel lines, eliminating blurry neumorphic shadows.
              </p>
            </div>

            {/* Paper-Cream (The Comic Page) */}
            <div className="bg-surface-card border border-border-charcoal p-5 space-y-4">
              <div className="text-xs font-mono uppercase text-paper-muted">Paper-Cream (The Page)</div>
              <div className="space-y-2">
                <div className="h-14 bg-paper-page border border-paper-border flex items-end p-2 text-[11px] font-mono text-paper-ink">
                  paper-page #F6F3EB (Editorial Page)
                </div>
                <div className="h-14 bg-paper-cream border border-paper-border flex items-end p-2 text-[11px] font-mono text-paper-ink">
                  paper-cream #FAF7F0 (Highlight)
                </div>
                <div className="h-14 bg-paper-warm border border-paper-border flex items-end p-2 text-[11px] font-mono text-paper-ink">
                  paper-warm #EFE9DC (Aged Tone)
                </div>
              </div>
              <p className="text-xs text-paper-muted font-sans leading-normal">
                High-contrast paper cream floating on charcoal. The visual signature of physical editorial print.
              </p>
            </div>

            {/* The One Accent: Vermilion */}
            <div className="bg-surface-card border border-border-charcoal p-5 space-y-4">
              <div className="text-xs font-mono uppercase text-vermilion-500 font-bold">The Single Accent</div>
              <div className="space-y-2">
                <div className="h-14 bg-vermilion-500 border border-vermilion-600 flex items-end p-2 text-[11px] font-mono text-white font-bold">
                  vermilion-500 #EA5A2C (Primary)
                </div>
                <div className="h-14 bg-vermilion-600 border border-vermilion-700 flex items-end p-2 text-[11px] font-mono text-white">
                  vermilion-600 #C9431D (Active/Press)
                </div>
                <div className="h-14 bg-vermilion-muted border border-vermilion-border flex items-end p-2 text-[11px] font-mono text-vermilion-500">
                  vermilion-muted (Glow/Muted)
                </div>
              </div>
              <p className="text-xs text-paper-muted font-sans leading-normal">
                Only vermilion gets color: critic failures, active states, primary actions. Nothing else competes.
              </p>
            </div>
          </div>
        </section>

        {/* ── 2. Typography Scale & Font Roles ─────────────────────────────── */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 border-b border-border-charcoal pb-3">
            <Type className="w-4 h-4 text-vermilion-500" />
            <h2 className="text-xl font-display font-semibold tracking-tight text-paper-cream">
              2. Typography Hierarchy & Roles
            </h2>
          </div>

          <div className="bg-surface-card border border-border-charcoal p-6 space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pb-6 border-b border-border-charcoal">
              <div>
                <div className="text-xs font-mono text-paper-muted uppercase mb-1">Display Headings</div>
                <div className="text-2xl font-display text-paper-cream">Newsreader</div>
                <p className="text-xs text-paper-muted mt-1">Editorial serif display face with optical sizing.</p>
              </div>
              <div>
                <div className="text-xs font-mono text-paper-muted uppercase mb-1">Humanist Body</div>
                <div className="text-2xl font-sans font-medium text-paper-cream">Inter</div>
                <p className="text-xs text-paper-muted mt-1">Clean, high-legibility UI and metadata face.</p>
              </div>
              <div>
                <div className="text-xs font-mono text-paper-muted uppercase mb-1">Artwork Lettering</div>
                <div className="text-2xl font-comic text-paper-cream tracking-wide">BANGERS ALL-CAPS</div>
                <p className="text-xs text-paper-muted mt-1">Reserved exclusively for dialogue inside artwork panels.</p>
              </div>
            </div>

            {/* Type Scale Demonstration */}
            <div className="space-y-5">
              <div className="flex flex-col md:flex-row md:items-baseline justify-between gap-2 border-b border-border-charcoal/50 pb-3">
                <span className="text-xs font-mono text-paper-muted w-32">Display 3XL</span>
                <span className="text-4xl font-display text-paper-cream tracking-tight flex-1">
                  Chapter I: The Beacon at the Edge of the World
                </span>
                <span className="text-xs font-mono text-paper-muted">36px / Newsreader</span>
              </div>

              <div className="flex flex-col md:flex-row md:items-baseline justify-between gap-2 border-b border-border-charcoal/50 pb-3">
                <span className="text-xs font-mono text-paper-muted w-32">Display 2XL</span>
                <span className="text-2xl font-display text-paper-cream tracking-tight flex-1">
                  Autonomous Visual Storytelling with Vision Critic
                </span>
                <span className="text-xs font-mono text-paper-muted">24px / Newsreader</span>
              </div>

              <div className="flex flex-col md:flex-row md:items-baseline justify-between gap-2 border-b border-border-charcoal/50 pb-3">
                <span className="text-xs font-mono text-paper-muted w-32">Body Large</span>
                <span className="text-base font-sans text-paper-cream leading-relaxed flex-1">
                  Inkwell coordinates specialized LLM and vision agents to design, storyboard, letter, and critique comic panels.
                </span>
                <span className="text-xs font-mono text-paper-muted">16px / Inter</span>
              </div>

              <div className="flex flex-col md:flex-row md:items-baseline justify-between gap-2 border-b border-border-charcoal/50 pb-3">
                <span className="text-xs font-mono text-paper-muted w-32">Body Regular</span>
                <span className="text-sm font-sans text-paper-muted leading-relaxed flex-1">
                  Comics are defined by hard panel edges, consistent character keyframes, and locked-in visual bibles.
                </span>
                <span className="text-xs font-mono text-paper-muted">14px / Inter</span>
              </div>

              <div className="flex flex-col md:flex-row md:items-baseline justify-between gap-2 pb-1">
                <span className="text-xs font-mono text-paper-muted w-32">Code & Metadata</span>
                <span className="text-xs font-mono text-vermilion-500 flex-1">
                  POST /projects/proj_8829/turn --model gemini-2.5-pro --cost-guard ACTIVE
                </span>
                <span className="text-xs font-mono text-paper-muted">12px / Monospace</span>
              </div>
            </div>
          </div>
        </section>

        {/* ── 3. The Comic Page on Desk (Visual Signature) ─────────────────── */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 border-b border-border-charcoal pb-3">
            <Layers className="w-4 h-4 text-vermilion-500" />
            <h2 className="text-xl font-display font-semibold tracking-tight text-paper-cream">
              3. The Signature Element: Floating Paper Page on Dark Desk
            </h2>
          </div>

          <div className="bg-ground-950 p-8 md:p-12 border border-border-charcoal flex justify-center">
            {/* The Floating Comic Page */}
            <div className="w-full max-w-md page-on-desk paper-grain-subtle p-6 space-y-4 transition-all duration-300 hover:shadow-[0_32px_64px_-16px_rgba(0,0,0,0.85),0_0_1px_1px_rgba(0,0,0,0.6)]">
              {/* Page Header */}
              <div className="flex justify-between items-center border-b border-paper-border pb-2 text-[10px] font-mono text-paper-muted">
                <span>INKWELL STUDIO ARCHIVE</span>
                <span>PAGE 01 • ACT I</span>
              </div>

              {/* 2-Panel Comic Layout Demo */}
              <div className="space-y-3">
                {/* Panel 1 */}
                <div className="h-44 bg-surface-card border-2 border-border-panel relative overflow-hidden flex flex-col justify-between p-3">
                  <div className="bg-paper-cream text-paper-ink text-[10px] font-sans font-medium px-2 py-1 border border-border-charcoal self-start">
                    The lighthouse keeper watches the storm.
                  </div>
                  <div className="self-end bg-white text-black px-3 py-1.5 rounded-full border-2 border-black font-comic text-xs tracking-wider shadow-sm">
                    ANOTHER FIERCE ONE...
                  </div>
                </div>

                {/* Panel 2 */}
                <div className="h-44 bg-surface-card border-2 border-border-panel relative overflow-hidden flex items-start justify-end p-3">
                  <div className="bg-white text-black px-3 py-1.5 rounded-full border-2 border-black font-comic text-xs tracking-wider shadow-sm">
                    NO! NOT NOW!
                  </div>
                </div>
              </div>

              {/* Page Footer */}
              <div className="text-center text-[9px] font-mono text-paper-muted pt-1">
                RENDERED ON PAPER-CREAM (#F6F3EB) FLOATING OVER WARM CHARCOAL (#1A1815)
              </div>
            </div>
          </div>
        </section>

        {/* ── 4. Motion Tokens Showcase (Interactive) ──────────────────────── */}
        <section className="space-y-6">
          <div className="flex items-center justify-between border-b border-border-charcoal pb-3">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-vermilion-500" />
              <h2 className="text-xl font-display font-semibold tracking-tight text-paper-cream">
                4. Motion Tokens (Interactive Eased Transitions)
              </h2>
            </div>
            <span className="text-xs font-mono text-paper-muted">No bounce • No spring • Eased precision</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* 200ms Fast Token */}
            <div className="bg-surface-card border border-border-charcoal p-5 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-paper-cream">200ms Fast Hover</span>
                <span className="text-[10px] font-mono text-paper-muted">motion-fast</span>
              </div>
              <p className="text-xs text-paper-muted">
                Used for micro-interactions, button hovers, and tag selections.
              </p>
              <div className="space-y-2 pt-2">
                <button className="w-full py-2.5 px-4 bg-surface-hover hover:bg-vermilion-500 hover:text-white text-xs font-medium border border-border-crisp motion-fast flex items-center justify-center gap-2">
                  <span>Hover to test 200ms transition</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* 400ms Panel Resolve Token */}
            <div className="bg-surface-card border border-border-charcoal p-5 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-paper-cream">400ms Panel Resolve</span>
                <span className="text-[10px] font-mono text-paper-muted">motion-panel</span>
              </div>
              <p className="text-xs text-paper-muted">
                Page frames exist first; panels resolve from blur-to-sharp into their frames.
              </p>
              <div className="pt-2 space-y-2">
                <div
                  className={`h-20 border-2 border-border-panel flex items-center justify-center text-xs font-mono motion-panel overflow-hidden ${
                    panelResolved
                      ? 'bg-surface-elevated text-paper-cream opacity-100 filter-none'
                      : 'bg-ground-950 text-paper-muted opacity-40 blur-[2px]'
                  }`}
                >
                  {panelResolved ? '✓ Panel Art Resolved (400ms)' : 'Empty Gutter Frame...'}
                </div>
                <button
                  onClick={triggerPanelResolve}
                  disabled={isResolving}
                  className="w-full py-1.5 px-3 bg-surface-card hover:bg-surface-hover border border-border-charcoal text-xs font-mono text-paper-cream motion-fast flex items-center justify-center gap-1.5"
                >
                  <Play className="w-3 h-3 text-vermilion-500" />
                  <span>{isResolving ? 'Resolving (400ms)...' : 'Test 400ms Resolve'}</span>
                </button>
              </div>
            </div>

            {/* 600ms Crossfade Token (Hero Critic Redraw) */}
            <div className="bg-surface-card border border-border-charcoal p-5 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono font-bold text-paper-cream">600ms Crossfade</span>
                <span className="text-[10px] font-mono text-paper-muted">motion-crossfade</span>
              </div>
              <p className="text-xs text-paper-muted">
                Critic failure detection crossfading smoothly into corrected redraw artwork.
              </p>
              <div className="pt-2 space-y-2">
                <div className="h-20 relative border border-border-charcoal overflow-hidden flex items-center justify-center text-xs font-mono">
                  {criticState === 'idle' && <span className="text-paper-muted">Panel Generated</span>}
                  {criticState === 'failed' && (
                    <div className="w-full h-full bg-ground-950/80 border-2 border-dashed border-vermilion-500 flex items-center justify-center text-vermilion-500 font-bold p-2 text-center text-[11px] animate-pulse">
                      ⚠ CRITIC FAILED: Style Drift
                    </div>
                  )}
                  {criticState === 'redrawing' && (
                    <div className="w-full h-full bg-vermilion-muted text-vermilion-500 flex items-center justify-center text-[11px] font-mono">
                      Redrawing with reference...
                    </div>
                  )}
                  {criticState === 'corrected' && (
                    <div className="w-full h-full bg-surface-elevated text-paper-cream flex items-center justify-center text-[11px] font-bold motion-crossfade">
                      ✓ Corrected Panel (600ms Crossfade)
                    </div>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={triggerCriticDemo}
                    className="flex-1 py-1.5 px-2 bg-vermilion-500 hover:bg-vermilion-600 text-white text-xs font-mono font-bold motion-fast flex items-center justify-center gap-1"
                  >
                    <Sliders className="w-3 h-3" />
                    <span>Run Critic Flow</span>
                  </button>
                  <button
                    onClick={resetCriticDemo}
                    className="p-1.5 bg-surface-card hover:bg-surface-hover border border-border-charcoal text-paper-muted hover:text-paper-cream motion-fast"
                    title="Reset"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── 5. Button & Component States ─────────────────────────────────── */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 border-b border-border-charcoal pb-3">
            <Sliders className="w-4 h-4 text-vermilion-500" />
            <h2 className="text-xl font-display font-semibold tracking-tight text-paper-cream">
              5. Component & Button States
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Buttons */}
            <div className="bg-surface-card border border-border-charcoal p-6 space-y-5">
              <h3 className="text-sm font-mono uppercase text-paper-muted tracking-wider">Button Hierarchy</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between gap-4">
                  <span className="text-xs font-mono text-paper-muted w-28">Primary (Vermilion)</span>
                  <button className="px-5 py-2.5 bg-vermilion-500 hover:bg-vermilion-600 active:bg-vermilion-700 text-white font-sans text-xs font-semibold tracking-wide motion-fast shadow-vermilion-glow">
                    Generate Comic Page
                  </button>
                </div>

                <div className="flex items-center justify-between gap-4">
                  <span className="text-xs font-mono text-paper-muted w-28">Secondary (Charcoal)</span>
                  <button className="px-5 py-2.5 bg-surface-card hover:bg-surface-hover active:bg-surface-active text-paper-cream border border-border-crisp font-sans text-xs font-medium motion-fast">
                    View Reference Sheet
                  </button>
                </div>

                <div className="flex items-center justify-between gap-4">
                  <span className="text-xs font-mono text-paper-muted w-28">Ghost / Subtle</span>
                  <button className="px-5 py-2.5 hover:bg-surface-hover text-paper-muted hover:text-paper-cream font-sans text-xs font-medium motion-fast">
                    Cancel Operation
                  </button>
                </div>

                <div className="flex items-center justify-between gap-4">
                  <span className="text-xs font-mono text-paper-muted w-28">Disabled State</span>
                  <button disabled className="px-5 py-2.5 bg-surface-card text-paper-muted/40 border border-border-charcoal/50 font-sans text-xs font-medium cursor-not-allowed">
                    Export Disabled
                  </button>
                </div>
              </div>
            </div>

            {/* Cards & Badges */}
            <div className="bg-surface-card border border-border-charcoal p-6 space-y-5">
              <h3 className="text-sm font-mono uppercase text-paper-muted tracking-wider">Card States & Status Badges</h3>
              <div className="space-y-3">
                {/* Default Surface Card */}
                <div className="p-3.5 bg-surface-card border border-border-charcoal flex items-center justify-between">
                  <span className="text-xs font-sans text-paper-cream">Default Surface Card</span>
                  <span className="px-2 py-0.5 text-[10px] font-mono bg-ground-900 border border-border-charcoal text-paper-muted">
                    1px Border
                  </span>
                </div>

                {/* Active Card */}
                <div className="p-3.5 bg-surface-card border-l-2 border-l-vermilion-500 border-t border-r border-b border-border-crisp flex items-center justify-between">
                  <span className="text-xs font-sans font-medium text-paper-cream">Active Selected Card</span>
                  <span className="px-2 py-0.5 text-[10px] font-mono bg-vermilion-muted text-vermilion-500 font-bold">
                    ACTIVE
                  </span>
                </div>

                {/* Critic Failed Card */}
                <div className="p-3.5 bg-ground-950 border-2 border-dashed border-vermilion-500 flex items-center justify-between opacity-80">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-vermilion-500" />
                    <span className="text-xs font-sans text-paper-cream font-medium">Critic Flagged: Needs Review</span>
                  </div>
                  <span className="verdict-pin text-[9px] font-mono px-2 py-0.5 uppercase tracking-wider">
                    STYLE DRIFT
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Footer ───────────────────────────────────────────────────────── */}
        <footer className="border-t border-border-charcoal pt-8 text-center text-xs font-mono text-paper-muted">
          INKWELL AI COMIC STUDIO • FOUNDATION DESIGN SYSTEM • CHUNK 1 COMPLETE
        </footer>
      </main>
    </div>
  );
}
