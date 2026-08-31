import React, { useState, useEffect } from 'react';
import { useProject } from './hooks/useProject';
import { CostBadge } from './components/CostBadge';
import { StoryIntake } from './components/StoryIntake';
import { StudioGrid } from './components/StudioGrid';
import { CriticFeed } from './components/CriticFeed';
import { CharacterGallery } from './components/CharacterGallery';
import { ComicReader } from './components/ComicReader';
import { ExportBar } from './components/ExportBar';
import { MotionTeaser } from './components/MotionTeaser';
import { StyleGuide } from './components/StyleGuide';
import { LiveSimulationController } from './components/LiveSimulationController';
import { ShaderGradientBackground } from './components/ShaderGradientBackground';
import {
  Feather,
  LayoutGrid,
  Users,
  BookOpen,
  Download,
  PlusCircle,
  Sparkles,
} from 'lucide-react';

export function App() {
  const [projectId, setProjectId] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      const urlProj = params.get('project') || params.get('projectId');
      if (urlProj) return urlProj;
      return localStorage.getItem('inkwell_active_project') || null;
    }
    return null;
  });
  const [activeTab, setActiveTab] = useState<'intake' | 'studio' | 'characters' | 'reader' | 'exports'>('intake');
  const [isStartingStory, setIsStartingStory] = useState(false);
  const [isGeneratingPipeline, setIsGeneratingPipeline] = useState(false);
  const [simulatedProject, setSimulatedProject] = useState<any | null>(null);

  // Check URL query param for standalone design system style-guide reference
  const isStyleGuideRoute = typeof window !== 'undefined' && window.location.search.includes('styleguide=true');

  const { project: liveProject, loading, createProject, sendTurn, approveItem, triggerGeneration } = useProject(projectId);

  // Active project is either simulated project or live project
  const project = simulatedProject || liveProject;

  // Sync active project to localStorage
  useEffect(() => {
    if (projectId) {
      localStorage.setItem('inkwell_active_project', projectId);
    } else {
      localStorage.removeItem('inkwell_active_project');
    }
  }, [projectId]);

  // Auto-switch to studio grid when drawing starts
  useEffect(() => {
    if (project?.status && ['drawing', 'lettering', 'laying_out', 'exporting'].includes(project.status)) {
      if (activeTab === 'intake') {
        setActiveTab('studio');
      }
    } else if (project?.status === 'done' && activeTab === 'studio') {
      setActiveTab('reader');
    }
  }, [project?.status]);

  // Start new project from story premise
  const handleStartStory = async (storyText: string) => {
    setIsStartingStory(true);
    setSimulatedProject(null);
    try {
      const newId = await createProject(storyText);
      if (newId) {
        setProjectId(newId);
        setActiveTab('intake');
      }
    } finally {
      setIsStartingStory(false);
    }
  };

  const handleTriggerGenerate = async () => {
    if (isGeneratingPipeline) return;
    setIsGeneratingPipeline(true);
    setSimulatedProject(null);
    try {
      await triggerGeneration();
      setActiveTab('studio');
    } catch (err) {
      console.error('[handleTriggerGenerate] error:', err);
    } finally {
      setIsGeneratingPipeline(false);
    }
  };

  const handleCreateNewProject = () => {
    setProjectId(null);
    setSimulatedProject(null);
    setActiveTab('intake');
  };

  // If style-guide is directly requested via ?styleguide=true, render it standalone
  if (isStyleGuideRoute) {
    return <StyleGuide />;
  }

  return (
    <div className={`flex flex-col h-screen ${activeTab === 'reader' ? 'bg-ground-900' : 'bg-transparent'} text-paper-cream font-sans selection:bg-vermilion-500 selection:text-white relative`}>
      {/* ── Ambient Background Shader (Full intensity on Intake hero, 0.65 on Studio/Characters/Exports, Hidden on Reader) ── */}
      {activeTab !== 'reader' && (
        <ShaderGradientBackground intensity={activeTab === 'intake' || !projectId ? 1.0 : 0.65} />
      )}

      {/* ── Top Navigation Bar ─────────────────────────────────────────────── */}
      <header
        className="h-14 border-b border-white/5 px-4 md:px-6 flex items-center justify-between shrink-0 z-20"
        style={{
          backgroundColor: 'rgba(26, 24, 21, 0.6)',
          backdropFilter: 'blur(20px) saturate(120%)',
          WebkitBackdropFilter: 'blur(20px) saturate(120%)',
        }}
      >
        {/* Brand */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleCreateNewProject}
            className="flex items-center gap-2 font-display text-xl font-bold tracking-tight text-paper-cream hover:text-white motion-fast text-left"
          >
            <span className="w-8 h-8 bg-vermilion-500 flex items-center justify-center text-white font-serif shadow-sm">
              ✒️
            </span>
            <span>InkWell</span>
          </button>

          <span className="hidden md:inline-block px-2 py-0.5 text-[10px] font-mono bg-surface-card border border-border-charcoal text-paper-muted uppercase">
            Collaborative Comic Studio
          </span>
        </div>

        {/* Phase Navigation Tabs — ONLY shown when a project is active */}
        {projectId && (
          <nav className="flex items-center gap-1 bg-ground-900 p-1 border border-border-charcoal">
            <button
              onClick={() => setActiveTab('intake')}
              className={`px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 motion-fast ${
                activeTab === 'intake'
                  ? 'bg-vermilion-500 text-white font-semibold'
                  : 'text-paper-muted hover:text-paper-cream hover:bg-surface-card'
              }`}
            >
              <Feather className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Story & Intake</span>
            </button>

            <button
              onClick={() => setActiveTab('studio')}
              className={`px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 motion-fast ${
                activeTab === 'studio'
                  ? 'bg-vermilion-500 text-white font-semibold'
                  : 'text-paper-muted hover:text-paper-cream hover:bg-surface-card'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Studio Grid</span>
            </button>

            <button
              onClick={() => setActiveTab('characters')}
              className={`px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 motion-fast ${
                activeTab === 'characters'
                  ? 'bg-vermilion-500 text-white font-semibold'
                  : 'text-paper-muted hover:text-paper-cream hover:bg-surface-card'
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Characters</span>
            </button>

            <button
              onClick={() => setActiveTab('reader')}
              className={`px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 motion-fast ${
                activeTab === 'reader'
                  ? 'bg-vermilion-500 text-white font-semibold'
                  : 'text-paper-muted hover:text-paper-cream hover:bg-surface-card'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Reader</span>
            </button>

            <button
              onClick={() => setActiveTab('exports')}
              className={`px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 motion-fast ${
                activeTab === 'exports'
                  ? 'bg-vermilion-500 text-white font-semibold'
                  : 'text-paper-muted hover:text-paper-cream hover:bg-surface-card'
              }`}
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Exports</span>
            </button>
          </nav>
        )}

        {/* Cost Guard & Project Actions */}
        <div className="flex items-center gap-3">
          {activeTab !== 'intake' && activeTab !== 'reader' && Boolean(projectId) && (
            <CostBadge
              costMode={project?.costMode || 'DEV'}
              imagesGenerated={project?.imagesGenerated || 0}
              estSpendUsd={project?.estSpendUsd || 0}
              showDetails={true}
            />
          )}

          {projectId && (
            <button
              onClick={handleCreateNewProject}
              className="px-2.5 py-1.5 border border-border-charcoal bg-surface-card hover:bg-surface-hover text-paper-cream text-xs flex items-center gap-1.5 motion-fast"
              title="Start a new comic story"
            >
              <PlusCircle className="w-3.5 h-3.5 text-vermilion-500" />
              <span className="hidden sm:inline">New Story</span>
            </button>
          )}
        </div>
      </header>

      {/* ── Main Workspace Body ────────────────────────────────────────────── */}
      <main className="flex-1 overflow-hidden p-4 md:p-6 relative z-10">
        {!projectId ? (
          /* Empty First Screen — Clean large textarea + invitation line */
          <StoryIntake
            project={null}
            onStartStory={handleStartStory}
            onSendMessage={sendTurn}
            onTriggerGenerate={handleTriggerGenerate}
            isGenerating={isGeneratingPipeline}
            isStarting={isStartingStory}
          />
        ) : (
          <div className="h-full">
            {/* TAB 1: STORY & INTAKE (Active Conversation & Story Bible) */}
            {activeTab === 'intake' && (
              <StoryIntake
                project={project}
                onStartStory={handleStartStory}
                onSendMessage={sendTurn}
                onTriggerGenerate={handleTriggerGenerate}
                isGenerating={isGeneratingPipeline}
              />
            )}

            {/* TAB 2: STUDIO GRID & LIVE CRITIC */}
            {activeTab === 'studio' && (
              <div className="h-full flex flex-col space-y-3">
                <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 overflow-hidden">
                  <div className="lg:col-span-8 h-full overflow-hidden">
                    <StudioGrid
                      panels={project?.panels || []}
                      pages={project?.pages || []}
                      characters={project?.characters || []}
                      progress={project?.progress || 0}
                      status={project?.status || 'idle'}
                      activeReferencedCharacter={
                        project?.status === 'drawing' ? 'Elara Thorne' : null
                      }
                      onApprovePanel={(id, decision, note) => approveItem('panel', id, decision, note)}
                      simulationControls={
                        <LiveSimulationController
                          onInjectMockProject={(p) => setSimulatedProject(p)}
                          onInjectStepUpdate={(updater) => setSimulatedProject((prev: any) => updater(prev || project))}
                          onReset={() => setSimulatedProject(null)}
                        />
                      }
                    />
                  </div>
                  <div className="lg:col-span-4 h-full overflow-hidden">
                    <CriticFeed traces={project?.traces || []} currentStatus={project?.status} />
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: CHARACTERS */}
            {activeTab === 'characters' && (
              <div className="h-full overflow-y-auto pr-2">
                <CharacterGallery
                  characters={project?.characters || []}
                  onApproveCharacter={(id, decision, note) => approveItem('character', id, decision, note)}
                />
              </div>
            )}

            {/* TAB 4: COMIC READER */}
            {activeTab === 'reader' && (
              <div className="h-full overflow-hidden flex flex-col">
                <ComicReader
                  pages={project?.pages || []}
                  panels={project?.panels || []}
                  title={project?.title || 'Inkwell Comic'}
                />
                {project?.result?.motionUri && (
                  <div className="mt-4">
                    <MotionTeaser
                      motionUri={project.result.motionUri}
                      title={project?.title || 'Inkwell Comic'}
                    />
                  </div>
                )}
              </div>
            )}

            {/* TAB 5: EXPORTS & DELIVERABLES */}
            {activeTab === 'exports' && (
              <div className="h-full overflow-y-auto pr-1 pb-6">
                {project && <ExportBar project={project} />}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
