import React from 'react';
import { Film, Music, Sparkles } from 'lucide-react';

interface MotionTeaserProps {
  motionUri?: string;
  soundtrackUri?: string;
  title: string;
}

export const MotionTeaser: React.FC<MotionTeaserProps> = ({ motionUri, soundtrackUri, title }) => {
  if (!motionUri && !soundtrackUri) {
    return (
      <div className="p-8 text-center bg-desk-900 border border-desk-700 rounded-xl text-paper-300 space-y-2">
        <Film className="w-8 h-8 mx-auto opacity-30" />
        <h4 className="text-sm font-semibold text-paper-100">Motion Teaser Gated to FINAL Mode</h4>
        <p className="text-xs max-w-sm mx-auto">
          Veo 3.1 video animation and Lyria music soundtrack scoring are produced when running in FINAL demo mode to conserve build budget.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-desk-800 border border-desk-700 rounded-xl p-4 shadow-xl space-y-4 max-w-2xl mx-auto">
      <div className="flex items-center justify-between border-b border-desk-700 pb-2">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-rose-400" />
          <h3 className="text-sm font-semibold text-paper-100 font-display">
            Veo 3.1 Motion Comic Teaser & Lyria Score
          </h3>
        </div>
        <span className="text-[10px] font-mono uppercase bg-rose-950/80 border border-rose-600/40 text-rose-300 px-2 py-0.5 rounded-full">
          Multimedia Teaser
        </span>
      </div>

      {/* Video Player */}
      {motionUri && (
        <div className="rounded-xl overflow-hidden bg-black aspect-video border border-desk-700 shadow-2xl">
          <video
            src={motionUri}
            controls
            autoPlay
            loop
            className="w-full h-full object-contain"
          />
        </div>
      )}

      {/* Soundtrack Player */}
      {soundtrackUri && (
        <div className="bg-desk-900 p-3 rounded-lg border border-desk-700 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-paper-200">
            <Music className="w-4 h-4 text-ink-gold" />
            <span>Lyria Background Score</span>
          </div>
          <audio src={soundtrackUri} controls className="h-8 w-64" />
        </div>
      )}
    </div>
  );
};
