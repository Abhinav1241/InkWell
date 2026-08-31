import React, { useState } from 'react';
import { ProjectData, Panel, Character, TraceEntry } from '../hooks/useProject';
import { Play, RotateCcw, Activity, ShieldAlert, Sparkles, FastForward } from 'lucide-react';

interface LiveSimulationControllerProps {
  onInjectMockProject: (project: ProjectData) => void;
  onInjectStepUpdate: (updater: (prev: ProjectData) => ProjectData) => void;
  onReset: () => void;
}

export const LiveSimulationController: React.FC<LiveSimulationControllerProps> = ({
  onInjectMockProject,
  onInjectStepUpdate,
  onReset,
}) => {
  const [isRunningSim, setIsRunningSim] = useState(false);
  const [activeStepName, setActiveStepName] = useState<string | null>(null);

  // ── Chunk 3 & 4 Verification Sequence: Live Data Payload Streaming & 400ms Panel Resolve
  const runLiveStreamingSimulation = async () => {
    setIsRunningSim(true);

    // Initial base project state (Empty Gutter Frames First)
    const baseProject: ProjectData = {
      id: 'sim_stream_001',
      status: 'planning',
      progress: 25,
      title: 'The Last Lighthouse Keeper',
      logline: 'An old lighthouse keeper named Elara discovers the light seals an ancient dark creature beneath the waves. During a catastrophic storm, the light fails, and she has one night to fix it.',
      options: {
        style: 'manga-influenced modern comic',
        pageCount: 6,
        rating: 'all-ages',
        aspect: '3:4',
        palette: 'vibrant maritime / warm vermilion',
        pacing: 'balanced',
      },
      costMode: 'DEV',
      imagesGenerated: 0,
      estSpendUsd: 0.0,
      characters: [
        {
          id: 'c1',
          name: 'Elara Thorne',
          role: 'protagonist',
          description: 'Weathered keeper in her 60s, heavy oilskin jacket, brass storm lantern, sharp discerning gaze.',
          referenceSheetUris: ['/mock_art/character_elara.png'],
          approved: true,
        },
        {
          id: 'c2',
          name: 'The Abyssal Leviathan',
          role: 'antagonist',
          description: 'Colossal bioluminescent sea creature sealed in the abyssal trench below the beacon.',
          referenceSheetUris: [],
          approved: true,
        },
      ],
      messages: [
        { id: 'm1', role: 'user', text: 'An old lighthouse keeper discovers the beacon seals a leviathan.' },
        { id: 'm2', role: 'agent', text: 'Story Bible locked. Characters designed. Initializing 4-panel empty layout frames.' },
      ],
      traces: [
        { id: 't1', stage: 'character_design', level: 'decision', message: '✓ Character reference sheets locked for Elara Thorne & Leviathan.', ts: Date.now() - 4000 },
        { id: 't2', stage: 'panel_planning', level: 'info', message: 'Script breakdown complete. Initializing empty gutter frames for Page 1.', ts: Date.now() - 2000 },
      ],
      panels: [
        {
          id: 'p1',
          pageIndex: 0,
          order: 0,
          shotType: 'ESTABLISHING WIDE',
          staging: 'Left to Right',
          charactersPresent: ['Elara Thorne'],
          action: 'The lighthouse tower stands battered by colossal ocean waves in the stormy night.',
          caption: 'The beacon at the edge of the world had never failed.',
          dialogue: [{ speaker: 'Elara Thorne', text: 'ANOTHER FIERCE ONE...', bubbleType: 'speech' }],
          status: 'pending',
          criticIterations: 0,
          criticNotes: [],
        },
        {
          id: 'p2',
          pageIndex: 0,
          order: 1,
          shotType: 'CLOSE-UP DRAMATIC',
          staging: 'Center',
          charactersPresent: ['Elara Thorne'],
          action: 'Elara peers anxiously through the rain-streaked lantern room window.',
          caption: 'Until tonight.',
          dialogue: [{ speaker: 'Elara Thorne', text: 'NO! NOT NOW!', bubbleType: 'speech' }],
          status: 'pending',
          criticIterations: 0,
          criticNotes: [],
        },
      ],
      pages: [],
      costs: [],
    };

    onInjectMockProject(baseProject);
    setActiveStepName('Step 1: Empty gutter frames initialized');

    // Step 2: Live Stream Payload 1 — Drawing Panel 1 (Consulting Character Memory Card)
    await new Promise((r) => setTimeout(r, 1200));
    setActiveStepName('Step 2: Live update — Drawing Panel 1 & Pulsing Elara Memory Card');
    onInjectStepUpdate((prev) => ({
      ...prev,
      status: 'drawing',
      progress: 45,
      traces: [
        ...prev.traces,
        {
          id: 't3',
          stage: 'panel_generation',
          level: 'info',
          message: 'Drawing Panel #1 (Wide): Consulting Elara Thorne character reference sheet for visual consistency.',
          ts: Date.now(),
        },
      ],
      panels: prev.panels.map((p, idx) =>
        idx === 0
          ? {
              ...p,
              status: 'drafted',
            }
          : p
      ),
    }));

    // Step 3: Panel 1 Resolves with 400ms Blur-to-Sharp animation
    await new Promise((r) => setTimeout(r, 1400));
    setActiveStepName('Step 3: Panel 1 Artwork Resolves (400ms blur-to-sharp)');
    onInjectStepUpdate((prev) => ({
      ...prev,
      progress: 60,
      imagesGenerated: 1,
      traces: [
        ...prev.traces,
        {
          id: 't4',
          stage: 'panel_generation',
          level: 'decision',
          message: '✓ Panel #1 artwork resolved into frame. Passed initial visual checks.',
          ts: Date.now(),
        },
      ],
      panels: prev.panels.map((p, idx) =>
        idx === 0
          ? {
              ...p,
              status: 'generated',
              artUri: '/mock_art/panel_1.png',
              letteredUri: '/mock_art/panel_1.png',
            }
          : p
      ),
    }));

    // Step 4: Chunk 5 — Critic Failure on Panel 2 (THE HERO)
    await new Promise((r) => setTimeout(r, 1800));
    setActiveStepName('Step 4: Panel 2 drawn — Triggering Critic Vision QA');
    onInjectStepUpdate((prev) => ({
      ...prev,
      progress: 75,
      imagesGenerated: 2,
      traces: [
        ...prev.traces,
        {
          id: 't5',
          stage: 'consistency_critic',
          level: 'warn',
          message: '⚠️ CRITIC REJECTED Panel #2: Style drift detected in facial structure & color palette compared to Elara reference sheet. Requesting auto-correction redraw pass 2.',
          data: {
            correctedPrompt: 'Maintain Elara Thorne canonical oilskin texture, sharpen jawline, correct lantern glow temperature.',
          },
          ts: Date.now(),
        },
      ],
      panels: prev.panels.map((p, idx) =>
        idx === 1
          ? {
              ...p,
              status: 'needs_review',
              criticIterations: 1,
              draftUri: '/mock_art/panel_rejected.png',
              artUri: '/mock_art/panel_rejected.png',
              criticNotes: [
                'Style drift & face geometry inconsistency detected against Character Reference Sheet (Pass 1). Autonomous redraw triggered.',
              ],
            }
          : p
      ),
    }));

    // Step 5: 600ms Crossfade to Corrected Redrawn Artwork
    await new Promise((r) => setTimeout(r, 2200));
    setActiveStepName('Step 5: 600ms Crossfade to Corrected Artwork & Verification Pass');
    onInjectStepUpdate((prev) => ({
      ...prev,
      status: 'lettering',
      progress: 95,
      imagesGenerated: 3,
      traces: [
        ...prev.traces,
        {
          id: 't6',
          stage: 'consistency_critic',
          level: 'decision',
          message: '✓ Panel #2 Redraw Pass 2 PASSED: Consistency score 0.94. Character keyframe locked.',
          ts: Date.now(),
        },
        {
          id: 't7',
          stage: 'lettering',
          level: 'info',
          message: 'Lettering applied with Bangers dialogue speech bubbles and Comic Neue narration caption boxes.',
          ts: Date.now() + 100,
        },
      ],
      panels: prev.panels.map((p, idx) =>
        idx === 1
          ? {
              ...p,
              status: 'approved',
              criticIterations: 2,
              draftUri: '/mock_art/panel_rejected.png',
              artUri: '/mock_art/panel_corrected.png',
              letteredUri: '/mock_art/panel_corrected.png',
              criticNotes: [
                'Redraw Pass 2 resolved face anatomy, lantern illumination, and hair consistency. Critic approved.',
              ],
            }
          : p
      ),
    }));

    await new Promise((r) => setTimeout(r, 1000));
    setActiveStepName('Complete: All real-time streams, 400ms resolve, and 600ms critic redraw verified.');
    setIsRunningSim(false);
  };

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={runLiveStreamingSimulation}
        disabled={isRunningSim}
        className="px-3 py-1.5 bg-vermilion-500 hover:bg-vermilion-600 disabled:opacity-50 text-white font-sans text-xs font-semibold flex items-center gap-1.5 motion-fast shadow-vermilion-glow"
      >
        <Play className="w-3.5 h-3.5" />
        <span>{isRunningSim ? 'Running Verification...' : 'Run Chunks 3–5 Full Interaction'}</span>
      </button>

      <button
        onClick={onReset}
        disabled={isRunningSim}
        className="px-2.5 py-1.5 bg-surface-card hover:bg-surface-hover border border-border-charcoal text-paper-cream text-xs flex items-center gap-1 motion-fast"
      >
        <RotateCcw className="w-3.5 h-3.5" />
        <span className="hidden sm:inline">Reset</span>
      </button>
    </div>
  );
};
