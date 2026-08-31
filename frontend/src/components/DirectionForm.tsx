import React from 'react';
import { ProjectData } from '../hooks/useProject';
import { Palette, BookOpen, Layers, ShieldCheck, Film } from 'lucide-react';

interface DirectionFormProps {
  project: ProjectData;
  onTriggerGeneration: () => void;
}

export const DirectionForm: React.FC<DirectionFormProps> = ({ project, onTriggerGeneration }) => {
  const options = project.options || {
    style: 'manga-influenced modern comic',
    pageCount: 6,
    rating: 'all-ages',
    aspect: '3:4',
    palette: 'vibrant',
    pacing: 'balanced',
  };

  return (
    <div className="bg-desk-800 border border-desk-700 rounded-xl p-4 shadow-xl space-y-4">
      <div className="flex items-center justify-between border-b border-desk-700 pb-3">
        <div>
          <h3 className="text-sm font-semibold text-paper-100 uppercase tracking-wider font-sans">
            Creative Direction & Story Bible
          </h3>
          <p className="text-xs text-paper-300">
            Locked from your collaborative interview with the Creative Director.
          </p>
        </div>
        <button
          onClick={onTriggerGeneration}
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-ink-blue to-indigo-600 hover:from-blue-600 hover:to-indigo-500 text-white text-xs font-semibold shadow-lg transition-all transform hover:scale-105"
        >
          Generate Comic Studio Pipeline
        </button>
      </div>

      {/* Logline */}
      {project.logline && (
        <div className="bg-desk-900/80 p-3 rounded-lg border border-desk-700/60">
          <span className="text-[10px] font-mono uppercase text-ink-blue block font-bold mb-1">
            Story Premise & Logline
          </span>
          <p className="text-xs text-paper-100 font-display italic leading-relaxed">
            "{project.logline}"
          </p>
        </div>
      )}

      {/* Grid of Direction Options */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
        <div className="bg-desk-900/60 p-2.5 rounded-lg border border-desk-700/50 space-y-1">
          <span className="flex items-center gap-1.5 text-paper-300 text-[10px] font-mono uppercase">
            <Palette className="w-3 h-3 text-ink-blue" />
            House Art Style
          </span>
          <strong className="text-paper-100 block capitalize">{options.style}</strong>
        </div>

        <div className="bg-desk-900/60 p-2.5 rounded-lg border border-desk-700/50 space-y-1">
          <span className="flex items-center gap-1.5 text-paper-300 text-[10px] font-mono uppercase">
            <BookOpen className="w-3 h-3 text-ink-gold" />
            Target Pages
          </span>
          <strong className="text-paper-100 block">{options.pageCount} Pages</strong>
        </div>

        <div className="bg-desk-900/60 p-2.5 rounded-lg border border-desk-700/50 space-y-1">
          <span className="flex items-center gap-1.5 text-paper-300 text-[10px] font-mono uppercase">
            <ShieldCheck className="w-3 h-3 text-emerald-400" />
            Content Rating
          </span>
          <strong className="text-paper-100 block uppercase">{options.rating}</strong>
        </div>

        <div className="bg-desk-900/60 p-2.5 rounded-lg border border-desk-700/50 space-y-1">
          <span className="flex items-center gap-1.5 text-paper-300 text-[10px] font-mono uppercase">
            <Layers className="w-3 h-3 text-purple-400" />
            Color Palette
          </span>
          <strong className="text-paper-100 block capitalize">{options.palette}</strong>
        </div>
      </div>
    </div>
  );
};
