import React from 'react';
import { Sparkles, ShieldAlert, Coins } from 'lucide-react';

interface CostBadgeProps {
  costMode: 'DEV' | 'PREVIEW' | 'FINAL';
  imagesGenerated?: number;
  maxImages?: number;
  estSpendUsd?: number;
  showDetails?: boolean;
}

export const CostBadge: React.FC<CostBadgeProps> = ({
  costMode,
  imagesGenerated = 0,
  maxImages = 40,
  estSpendUsd = 0,
  showDetails = true,
}) => {
  const isCapped = imagesGenerated >= maxImages;

  // Pure read-only status badge styles (no hover, no cursor pointer, no button semantics)
  const modeColor = {
    DEV: 'bg-emerald-950/70 border-emerald-500/40 text-emerald-300',
    PREVIEW: 'bg-amber-950/70 border-amber-500/40 text-amber-300',
    FINAL: 'bg-rose-950/70 border-rose-500/40 text-rose-300',
  }[costMode] || 'bg-surface-card border-border-charcoal text-paper-cream';

  return (
    <div className="flex items-center gap-2 text-xs font-mono select-none" role="status" aria-label={`Cost Guard: ${costMode} mode`}>
      {/* Mode Status Indicator (Read-Only Badge) */}
      <span className={`px-2.5 py-1 rounded-full border flex items-center gap-1.5 text-[11px] font-mono tracking-wider font-semibold cursor-default ${modeColor}`}>
        <Sparkles className="w-3 h-3 text-emerald-400" />
        <span>{costMode} MODE</span>
      </span>

      {/* Cap Counter & Spend Readout — Only visible on pipeline pages */}
      {showDetails && (
        <>
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full border cursor-default ${
              isCapped
                ? 'bg-red-950/80 border-red-500/60 text-red-300'
                : 'bg-surface-card border-border-charcoal text-paper-cream'
            }`}
            title="Image Generation Cap"
          >
            {isCapped && <ShieldAlert className="w-3 h-3 text-red-400 animate-pulse" />}
            <span>{imagesGenerated}/{maxImages} images</span>
          </div>

          <div
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-surface-card border border-border-charcoal text-paper-cream cursor-default"
            title="Estimated Model API Spend"
          >
            <Coins className="w-3 h-3 text-vermilion-500" />
            <span>${estSpendUsd.toFixed(3)} est.</span>
          </div>
        </>
      )}
    </div>
  );
};
