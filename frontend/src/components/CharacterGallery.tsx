import React, { useState } from 'react';
import { Character } from '../hooks/useProject';
import { resolveAssetUri } from '../utils/assets';
import { Check, X, Sparkles, User, RefreshCw, Layers, ShieldCheck } from 'lucide-react';

interface CharacterGalleryProps {
  characters: Character[];
  onApproveCharacter: (charId: string, decision: 'approve' | 'reject', note?: string) => void;
}

export const CharacterGallery: React.FC<CharacterGalleryProps> = ({
  characters,
  onApproveCharacter,
}) => {
  const [rejectNote, setRejectNote] = useState<{ [id: string]: string }>({});
  const [rejectingId, setRejectingId] = useState<string | null>(null);

  const handleReject = (charId: string) => {
    const note = rejectNote[charId] || 'Needs refinement';
    onApproveCharacter(charId, 'reject', note);
    setRejectingId(null);
  };

  // Fallback demo characters if empty
  const displayCharacters: Character[] =
    characters.length > 0
      ? characters
      : [
          {
            id: 'c1',
            name: 'Elara Thorne',
            role: 'protagonist',
            description:
              'Weathered lighthouse keeper in her 60s, heavy yellow-ochre oilskin coat, brass storm lantern, silver-grey swept hair, sharp discerning gaze.',
            canonicalPromptFragment:
              'Elara Thorne, elderly 60s female lighthouse keeper, weathered face, heavy yellow oilskin maritime jacket, holding brass storm lantern, sharp grey eyes, comic illustration.',
            referenceSheetUris: ['/mock_art/character_elara.png'],
            approved: true,
          },
          {
            id: 'c2',
            name: 'The Abyssal Leviathan',
            role: 'antagonist',
            description:
              'Colossal bioluminescent sea creature sealed in the abyssal trench below the beacon tower. Ancient barnacled scales, glowing cyan ridges.',
            canonicalPromptFragment:
              'Ancient abyssal sea leviathan, bioluminescent cyan ridges, colossal silhouette under dark stormy ocean waves, mythic comic art.',
            referenceSheetUris: [],
            approved: true,
          },
        ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div
        className="border border-border-charcoal p-6 flex flex-col md:flex-row md:items-center justify-between gap-4"
        style={{
          backgroundColor: 'rgba(26, 24, 21, 0.80)',
          backdropFilter: 'blur(16px)',
          WebkitBackdropFilter: 'blur(16px)',
        }}
      >
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] font-mono uppercase tracking-wider text-vermilion-500 font-bold px-2 py-0.5 bg-ground-950 border border-border-charcoal">
              Story Bible Memory Bank
            </span>
            <span className="text-xs font-mono text-paper-muted">Identity Locking</span>
          </div>
          <h2 className="text-xl font-display font-bold text-paper-cream">
            Character Turnaround Reference Sheets
          </h2>
          <p className="text-xs text-paper-muted font-sans mt-0.5">
            Locked visual reference keyframes passed to every downstream panel to ensure identity consistency.
          </p>
        </div>

        <span className="text-xs font-mono text-paper-cream bg-ground-950 border border-border-charcoal px-3 py-1.5 shrink-0 flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-vermilion-500" />
          <span>{displayCharacters.length} Cast Members Locked</span>
        </span>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {displayCharacters.map((char) => {
          const hasSheet = char.referenceSheetUris && char.referenceSheetUris.length > 0;
          const sheetSrc = hasSheet ? resolveAssetUri(char.referenceSheetUris[0]) : undefined;

          return (
            <div
              key={char.id}
              className="border border-border-charcoal overflow-hidden shadow-sm flex flex-col justify-between group hover:border-border-crisp motion-fast"
              style={{
                backgroundColor: 'rgba(26, 24, 21, 0.80)',
                backdropFilter: 'blur(16px)',
                WebkitBackdropFilter: 'blur(16px)',
              }}
            >
              {/* Header */}
              <div className="p-4 bg-ground-950 border-b border-border-charcoal flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-paper-cream text-base font-display">{char.name}</h3>
                  <span className="text-[10px] font-mono uppercase text-vermilion-500 bg-surface-card px-1.5 py-0.5 border border-border-charcoal mt-1 inline-block">
                    {char.role}
                  </span>
                </div>
                {char.approved ? (
                  <span className="px-2.5 py-1 text-[10px] font-mono bg-emerald-950/80 border border-emerald-500/60 text-emerald-300 flex items-center gap-1">
                    <ShieldCheck className="w-3.5 h-3.5" /> Canonical Memory Locked
                  </span>
                ) : (
                  <span className="px-2 py-0.5 text-[10px] font-mono bg-surface-card border border-border-charcoal text-paper-muted flex items-center gap-1">
                    <Sparkles className="w-3 h-3 text-vermilion-500" /> In Review
                  </span>
                )}
              </div>

              {/* Turnaround Sheet Preview */}
              <div className="relative aspect-[4/3] bg-ground-900 flex items-center justify-center overflow-hidden border-b border-border-charcoal">
                {sheetSrc ? (
                  <img
                    src={sheetSrc}
                    alt={`${char.name} reference sheet`}
                    className="w-full h-full object-cover group-hover:scale-[1.02] motion-fast"
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center p-6 text-center space-y-2 text-paper-muted">
                    <User className="w-8 h-8 opacity-40 text-border-crisp" />
                    <span className="text-xs font-mono uppercase">Reference Sheet In Pipeline</span>
                  </div>
                )}
              </div>

              {/* Canonical Prompt Fragment & Details */}
              <div className="p-4 space-y-3 text-xs bg-surface-card">
                <div>
                  <span className="text-[10px] font-mono uppercase text-paper-muted block mb-1">
                    Canonical Memory Prompt Fragment:
                  </span>
                  <p className="text-paper-cream bg-ground-950 p-2.5 border border-border-charcoal text-[11px] font-mono leading-relaxed">
                    {char.canonicalPromptFragment || char.description}
                  </p>
                </div>

                <div className="text-[11px] text-paper-muted leading-relaxed font-sans">
                  <strong className="text-paper-cream font-mono uppercase text-[10px] block mb-0.5">Role Biography:</strong>
                  {char.description}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
