import React, { useState } from 'react';
import { ProjectData } from '../hooks/useProject';
import {
  Download,
  FileCode,
  Share2,
  Film,
  Check,
  FileText,
  Layers,
  Sparkles,
  ShieldCheck,
  DollarSign,
  ExternalLink,
} from 'lucide-react';

interface ExportBarProps {
  project: ProjectData;
}

export const ExportBar: React.FC<ExportBarProps> = ({ project }) => {
  const result = project.result || {};
  const [copied, setCopied] = useState(false);
  const [downloadingPdf, setDownloadingPdf] = useState(false);

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownloadBible = () => {
    const bibleData = {
      title: project.title || 'Inkwell Comic',
      logline: project.logline,
      options: project.options,
      characters: project.characters,
      panels: project.panels,
      pages: project.pages,
      exportedAt: new Date().toISOString(),
      studioEngine: 'InkWell Autonomous Comic Studio',
    };
    const blob = new Blob([JSON.stringify(bibleData, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${(project.title || 'comic').toLowerCase().replace(/\s+/g, '_')}_story_bible.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const pdfUri = result.pdfUri || '/mock_art/comic.pdf';
  const hasPages = project.pages && project.pages.length > 0;
  const isFinished = project.status === 'exporting' || project.status === 'done' || hasPages || project.panels.length > 0;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Top Header Card */}
      <div
        className="border border-border-charcoal p-6 flex flex-col md:flex-row md:items-center justify-between gap-4"
        style={{
          backgroundColor: 'rgba(26, 24, 21, 0.60)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
        }}
      >
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-vermilion-500 font-bold px-2 py-0.5 bg-ground-950 border border-border-charcoal">
              Production Exports
            </span>
            <span className="text-xs font-mono text-paper-muted">Project: {project.id}</span>
          </div>
          <h2 className="text-xl font-display font-bold text-paper-cream">
            Studio Deliverables & Archival Artifacts
          </h2>
          <p className="text-xs text-paper-muted font-sans mt-0.5">
            Download high-resolution print PDF, agent memory sidecar JSON, and preview multimedia teasers.
          </p>
        </div>

        <button
          onClick={handleShare}
          className="px-3.5 py-2 bg-ground-950 hover:bg-surface-card border border-border-crisp text-paper-cream text-xs font-mono flex items-center gap-2 motion-fast shrink-0 shadow-sm focus:outline-none focus:ring-2 focus:ring-vermilion-500"
          aria-label="Share project link"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400">Link Copied!</span>
            </>
          ) : (
            <>
              <Share2 className="w-3.5 h-3.5 text-vermilion-500" />
              <span>Share Project</span>
            </>
          )}
        </button>
      </div>

      {/* ── Deliverables 3-Card Grid ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Card 1: High-Res Comic PDF */}
        <div
          className="border border-border-charcoal p-5 flex flex-col justify-between space-y-4 relative group hover:border-border-crisp motion-fast"
          style={{
            backgroundColor: 'rgba(26, 24, 21, 0.60)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
          }}
        >
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase text-emerald-400 font-bold px-1.5 py-0.5 bg-emerald-950/60 border border-emerald-800/40">
                Print Document
              </span>
              <FileText className="w-4 h-4 text-emerald-400" />
            </div>
            <h3 className="text-base font-display font-semibold text-paper-cream">
              High-Res Comic PDF
            </h3>
            <p className="text-xs text-paper-muted font-sans leading-relaxed">
              Multi-page vector-typeset PDF with Bangers dialogue, Comic Neue captions, and full 300 DPI layout.
            </p>
            <div className="pt-2 text-[11px] font-mono text-paper-muted space-y-1">
              <div>• Format: Standard Comic (A4/Letter)</div>
              <div>• Pages: {project.options?.pageCount || 6} Pages Stitch</div>
              <div>• Lettering: Compositor Lettered</div>
            </div>
          </div>

          <div className="pt-3 border-t border-border-charcoal">
            <a
              href={pdfUri}
              target="_blank"
              rel="noopener noreferrer"
              download={`${(project.title || 'comic').toLowerCase().replace(/\s+/g, '_')}.pdf`}
              className="w-full py-2.5 px-4 bg-emerald-700 hover:bg-emerald-600 text-white text-xs font-mono font-semibold flex items-center justify-center gap-2 motion-fast shadow-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <Download className="w-3.5 h-3.5" />
              Download Comic PDF
            </a>
          </div>
        </div>

        {/* Card 2: Story Bible JSON Sidecar */}
        <div
          className="border border-border-charcoal p-5 flex flex-col justify-between space-y-4 relative group hover:border-border-crisp motion-fast"
          style={{
            backgroundColor: 'rgba(26, 24, 21, 0.60)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
          }}
        >
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase text-vermilion-500 font-bold px-1.5 py-0.5 bg-vermilion-500/20 border border-vermilion-500/40">
                Agent Memory Sidecar
              </span>
              <FileCode className="w-4 h-4 text-vermilion-500" />
            </div>
            <h3 className="text-base font-display font-semibold text-paper-cream">
              Story Bible Sidecar
            </h3>
            <p className="text-xs text-paper-muted font-sans leading-relaxed">
              Complete machine-readable JSON containing character reference bibles, shot blueprints, and prompt lineages.
            </p>
            <div className="pt-2 text-[11px] font-mono text-paper-muted space-y-1">
              <div>• Characters: {project.characters?.length || 2} Profiles</div>
              <div>• Critic Notes: {project.traces?.length || 0} Reasoning Steps</div>
              <div>• Format: Standard InkWell JSON</div>
            </div>
          </div>

          <div className="pt-3 border-t border-border-charcoal">
            <button
              onClick={handleDownloadBible}
              className="w-full py-2.5 px-4 bg-surface-base hover:bg-surface-hover border border-border-crisp text-paper-cream text-xs font-mono font-semibold flex items-center justify-center gap-2 motion-fast shadow-md focus:outline-none focus:ring-2 focus:ring-vermilion-500"
            >
              <FileCode className="w-3.5 h-3.5 text-vermilion-500" />
              Export Bible JSON
            </button>
          </div>
        </div>

        {/* Card 3: Veo Motion Teaser */}
        <div
          className="border border-border-charcoal p-5 flex flex-col justify-between space-y-4 relative group hover:border-border-crisp motion-fast"
          style={{
            backgroundColor: 'rgba(26, 24, 21, 0.60)',
            backdropFilter: 'blur(16px)',
            WebkitBackdropFilter: 'blur(16px)',
          }}
        >
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase text-purple-400 font-bold px-1.5 py-0.5 bg-purple-950/60 border border-purple-800/40">
                Bonus Model Pack
              </span>
              <Film className="w-4 h-4 text-purple-400" />
            </div>
            <h3 className="text-base font-display font-semibold text-paper-cream">
              Veo Motion Teaser
            </h3>
            <p className="text-xs text-paper-muted font-sans leading-relaxed">
              AI cinematic video clip generated from the hero panel keyframe with Lyria musical score.
            </p>
            <div className="pt-2 text-[11px] font-mono text-paper-muted space-y-1">
              <div>• Video Engine: Google Veo (Gated)</div>
              <div>• Audio Engine: Google Lyria</div>
              <div>• Mode: FINAL Production Run</div>
            </div>
          </div>

          <div className="pt-3 border-t border-border-charcoal">
            {result.motionUri ? (
              <a
                href={result.motionUri}
                target="_blank"
                rel="noopener noreferrer"
                download="teaser.mp4"
                className="w-full py-2.5 px-4 bg-purple-700 hover:bg-purple-600 text-white text-xs font-mono font-semibold flex items-center justify-center gap-2 motion-fast shadow-md"
              >
                <Film className="w-3.5 h-3.5" />
                Watch Motion Teaser
              </a>
            ) : (
              <div className="w-full py-2.5 px-3 bg-ground-950 border border-border-charcoal text-paper-muted text-xs font-mono text-center">
                Available in FINAL Run
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Spend Ledger & Audit Trail ─────────────────────────────────────── */}
      <div
        className="border border-border-charcoal p-6 space-y-4"
        style={{
          backgroundColor: 'rgba(26, 24, 21, 0.60)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
        }}
      >
        <div className="flex items-center justify-between border-b border-border-charcoal pb-3">
          <div>
            <h3 className="text-sm font-display font-semibold text-paper-cream flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-vermilion-500" />
              Spend Ledger & Model Audit Trail
            </h3>
            <p className="text-xs text-paper-muted font-sans mt-0.5">
              Exact budget accountability, image generation counters, and model cost routing.
            </p>
          </div>
          <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/40 px-2 py-0.5">
            BUDGET PROTECTED
          </span>
        </div>

        {/* 4 Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-ground-950 p-3.5 border border-border-charcoal">
            <span className="text-paper-muted block text-[10px] font-mono uppercase">Cost Mode</span>
            <strong className="text-emerald-400 font-mono text-base">{project.costMode || 'DEV'}</strong>
            <span className="text-[9px] text-paper-muted block mt-0.5">Zero API spend in DEV</span>
          </div>

          <div className="bg-ground-950 p-3.5 border border-border-charcoal">
            <span className="text-paper-muted block text-[10px] font-mono uppercase">Total Generations</span>
            <strong className="text-paper-cream font-mono text-base">
              {project.imagesGenerated || 0} / 40
            </strong>
            <span className="text-[9px] text-paper-muted block mt-0.5">Hard cap enforced</span>
          </div>

          <div className="bg-ground-950 p-3.5 border border-border-charcoal">
            <span className="text-paper-muted block text-[10px] font-mono uppercase">Estimated Spend</span>
            <strong className="text-vermilion-500 font-mono text-base">
              ${(project.estSpendUsd || 0).toFixed(3)}
            </strong>
            <span className="text-[9px] text-paper-muted block mt-0.5">Real-time ledger</span>
          </div>

          <div className="bg-ground-950 p-3.5 border border-border-charcoal">
            <span className="text-paper-muted block text-[10px] font-mono uppercase">Pipeline Phase</span>
            <strong className="text-paper-cream font-mono text-base uppercase">
              {project.status || 'READY'}
            </strong>
            <span className="text-[9px] text-paper-muted block mt-0.5">Self-healing enabled</span>
          </div>
        </div>

        {/* Model Execution Routing Table */}
        <div className="overflow-x-auto pt-2">
          <table className="w-full text-left font-mono text-xs border border-border-charcoal">
            <thead className="bg-ground-950 text-[10px] uppercase text-paper-muted border-b border-border-charcoal">
              <tr>
                <th className="p-2.5">Pipeline Stage</th>
                <th className="p-2.5">Assigned Model</th>
                <th className="p-2.5">Role</th>
                <th className="p-2.5">Cost Guard</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-charcoal bg-ground-950/60 text-[11px] text-paper-cream">
              <tr>
                <td className="p-2.5">Creative Director</td>
                <td className="p-2.5 text-vermilion-500">Gemini 3.5 Flash</td>
                <td className="p-2.5 font-sans">Story extraction & script blueprinting</td>
                <td className="p-2.5 text-emerald-400">Enabled</td>
              </tr>
              <tr>
                <td className="p-2.5">Panel Artist</td>
                <td className="p-2.5 text-vermilion-500">Imagen 3 (Fast)</td>
                <td className="p-2.5 font-sans">Character sheet & panel generation</td>
                <td className="p-2.5 text-emerald-400">Max 40 images</td>
              </tr>
              <tr>
                <td className="p-2.5">Consistency Critic</td>
                <td className="p-2.5 text-vermilion-500">Gemini 3.5 Flash Vision</td>
                <td className="p-2.5 font-sans">Visual QA & auto-correction prompt delta</td>
                <td className="p-2.5 text-emerald-400">Max 2 passes</td>
              </tr>
              <tr>
                <td className="p-2.5">Compositor</td>
                <td className="p-2.5 text-emerald-400">Local PIL / PyMuPDF</td>
                <td className="p-2.5 font-sans">Bangers / Comic Neue lettering & PDF assembly</td>
                <td className="p-2.5 text-paper-muted">$0.00 (Local)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
