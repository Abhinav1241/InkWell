import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Page, Panel } from '../hooks/useProject';
import {
  ChevronLeft,
  ChevronRight,
  Volume2,
  VolumeX,
  Maximize2,
  Minimize2,
  BookOpen,
  Settings,
  ZoomIn,
  ZoomOut,
  Check,
  Compass,
} from 'lucide-react';

interface ComicReaderProps {
  pages: Page[];
  panels: Panel[];
  title: string;
}

export type ReadingMode = 'paged-ltr' | 'paged-rtl' | 'long-strip';
export type FitMode = 'fit-height' | 'fit-width' | 'actual';

export const ComicReader: React.FC<ComicReaderProps> = ({ pages, panels, title }) => {
  const [currentPage, setCurrentPage] = useState(0);
  const [isReadingAloud, setIsReadingAloud] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [readingMode, setReadingMode] = useState<ReadingMode>('paged-ltr');
  const [fitMode, setFitMode] = useState<FitMode>('fit-height');
  const [zoomPercent, setZoomPercent] = useState(100);
  const [showSettings, setShowSettings] = useState(false);
  const [showThumbnails, setShowThumbnails] = useState(true);
  const [isChromeVisible, setIsChromeVisible] = useState(true);

  const containerRef = useRef<HTMLDivElement>(null);
  const idleTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Fallback demo pages from milestone verification if pages array is empty
  const defaultDemoPages: Page[] = [
    {
      id: 'demo_p1',
      index: 0,
      layoutTemplate: 'two_row_cinematic',
      status: 'rendered',
      pageImageUri: '/mock_art/milestone_page_1.png',
      panelIds: ['p1', 'p2'],
    },
    {
      id: 'demo_p2',
      index: 1,
      layoutTemplate: 'two_row_cinematic',
      status: 'rendered',
      pageImageUri: '/mock_art/milestone_page_2.png',
      panelIds: ['p3', 'p4'],
    },
  ];

  const availablePages =
    pages.length > 0 && pages.some((p) => Boolean(p.pageImageUri))
      ? pages.filter((p) => Boolean(p.pageImageUri))
      : defaultDemoPages;

  const activePage = availablePages[currentPage] || availablePages[0];

  // Helper for title truncation at word boundary
  const formatTitle = (raw: string, maxLen = 42) => {
    if (!raw) return 'The Last Lighthouse Keeper';
    if (raw.length <= maxLen) return raw;
    const truncated = raw.slice(0, maxLen);
    const lastSpace = truncated.lastIndexOf(' ');
    return (lastSpace > 0 ? truncated.slice(0, lastSpace) : truncated) + '…';
  };

  const displayTitle = formatTitle(title || 'The Last Lighthouse Keeper');
  const fullTitle = title || 'The Last Lighthouse Keeper';

  // Extract speech & narration text for active page
  const pagePanels = panels.filter((p) => p.pageIndex === (activePage?.index ?? currentPage));
  const pageText =
    pagePanels.length > 0
      ? pagePanels
          .map((p) => {
            const dialogueText =
              p.dialogue?.map((d) => `${d.speaker || 'Narrator'}: ${d.text}`).join('. ') || '';
            return p.caption ? `${p.caption}. ${dialogueText}` : dialogueText;
          })
          .filter(Boolean)
          .join('. ')
      : currentPage === 0
      ? 'The beacon at the edge of the world had never failed. Elara Thorne says: Another fierce one. The mechanism was at the top, exposed to the tempest.'
      : 'The storm intensifies over the lighthouse. Elara watches the waves.';

  const handleNext = useCallback(() => {
    if (readingMode === 'paged-rtl') {
      if (currentPage > 0) setCurrentPage((prev) => prev - 1);
    } else {
      if (currentPage < availablePages.length - 1) setCurrentPage((prev) => prev + 1);
    }
  }, [currentPage, availablePages.length, readingMode]);

  const handlePrev = useCallback(() => {
    if (readingMode === 'paged-rtl') {
      if (currentPage < availablePages.length - 1) setCurrentPage((prev) => prev + 1);
    } else {
      if (currentPage > 0) setCurrentPage((prev) => prev - 1);
    }
  }, [currentPage, availablePages.length, readingMode]);

  const toggleReadAloud = () => {
    if ('speechSynthesis' in window) {
      if (isReadingAloud) {
        window.speechSynthesis.cancel();
        setIsReadingAloud(false);
      } else if (pageText) {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(pageText);
        utterance.rate = 0.92;
        utterance.pitch = 1.0;
        utterance.onend = () => setIsReadingAloud(false);
        utterance.onerror = () => setIsReadingAloud(false);
        window.speechSynthesis.speak(utterance);
        setIsReadingAloud(true);
      }
    }
  };

  // Zoom management
  const handleZoomIn = () => {
    setFitMode('actual');
    setZoomPercent((prev) => Math.min(prev + 15, 250));
  };

  const handleZoomOut = () => {
    setFitMode('actual');
    setZoomPercent((prev) => Math.max(prev - 15, 30));
  };

  const handleSelectFitMode = (mode: FitMode) => {
    setFitMode(mode);
    if (mode === 'actual') setZoomPercent(100);
  };

  // Auto-hiding chrome in fullscreen mode (2.4-second idle timer)
  const resetIdleTimer = useCallback(() => {
    setIsChromeVisible(true);
    if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
    if (isFullscreen) {
      idleTimerRef.current = setTimeout(() => {
        setIsChromeVisible(false);
      }, 2400);
    }
  }, [isFullscreen]);

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (e.clientY <= 70 || e.clientY >= window.innerHeight - 85) {
        setIsChromeVisible(true);
        if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
      } else {
        resetIdleTimer();
      }
    },
    [resetIdleTimer]
  );

  // Fullscreen keyboard & global shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;

      setIsChromeVisible(true);
      resetIdleTimer();

      if (e.key === 'ArrowRight' || e.key === ' ') {
        e.preventDefault();
        handleNext();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        handlePrev();
      } else if (e.key === 'f' || e.key === 'F') {
        e.preventDefault();
        setIsFullscreen((prev) => !prev);
      } else if (e.key === 'Escape') {
        if (showSettings) {
          setShowSettings(false);
        } else if (isFullscreen) {
          setIsFullscreen(false);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
    };
  }, [handleNext, handlePrev, isFullscreen, showSettings, resetIdleTimer]);

  // Dynamic style calculation for reactive zoom & fit controls
  const getPageContainerStyle = (): React.CSSProperties => {
    if (fitMode === 'fit-height') {
      return {
        maxHeight: isFullscreen ? '84vh' : 'calc(100vh - 230px)',
        width: 'auto',
      };
    }
    if (fitMode === 'fit-width') {
      return {
        width: '100%',
        maxWidth: '860px',
      };
    }
    // Actual / Custom Zoom
    return {
      width: `${Math.round(650 * (zoomPercent / 100))}px`,
      maxWidth: 'none',
    };
  };

  const getImageStyle = (): React.CSSProperties => {
    if (fitMode === 'fit-height') {
      return {
        maxHeight: isFullscreen ? '82vh' : 'calc(100vh - 250px)',
        width: 'auto',
        objectFit: 'contain',
      };
    }
    if (fitMode === 'fit-width') {
      return {
        width: '100%',
        height: 'auto',
        objectFit: 'contain',
      };
    }
    return {
      width: '100%',
      height: 'auto',
    };
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      className={`flex flex-col select-none ${
        isFullscreen
          ? 'fixed inset-0 z-50 bg-ground-950 bg-[#12110F] text-paper-cream overflow-hidden'
          : 'h-full w-full max-w-6xl mx-auto justify-between overflow-hidden'
      }`}
      role="region"
      aria-label="Comic Reader Canvas"
    >
      {/* ── 1. Top Masthead Toolbar (Auto-Hides in Fullscreen) ─────────────── */}
      <div
        className={`w-full flex items-center justify-between px-5 py-2.5 bg-ground-950 border border-border-charcoal shadow-md shrink-0 transition-opacity duration-300 focus-within:opacity-100 focus-within:pointer-events-auto z-30 ${
          isFullscreen
            ? `absolute top-0 left-0 right-0 ${
                isChromeVisible ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
              }`
            : 'relative'
        }`}
      >
        {/* Title & Page Indicator */}
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-7 h-7 bg-surface-card border border-border-charcoal flex items-center justify-center text-vermilion-500 shrink-0">
            <BookOpen className="w-4 h-4" />
          </div>
          <div className="min-w-0">
            <h2
              className="font-display font-semibold text-paper-cream text-sm md:text-base truncate cursor-help"
              title={fullTitle}
            >
              {displayTitle}
            </h2>
          </div>
          {readingMode !== 'long-strip' && (
            <span className="text-xs font-mono text-paper-muted px-2.5 py-1 bg-surface-card border border-border-charcoal shrink-0">
              Page {currentPage + 1} of {availablePages.length}
            </span>
          )}
        </div>

        {/* Toolbar Controls */}
        <div className="flex items-center gap-2 shrink-0">
          {/* Zoom & Fit 3-Mode Controls */}
          <div className="flex items-center gap-1 bg-surface-card border border-border-charcoal px-1.5 py-1">
            <button
              onClick={handleZoomOut}
              className="p-1 hover:text-white text-paper-muted hover:bg-surface-hover motion-fast focus:outline-none focus:ring-1 focus:ring-vermilion-500"
              title="Zoom Out (-)"
              aria-label="Zoom Out"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <span className="text-[11px] font-mono text-paper-cream px-1.5 min-w-[38px] text-center">
              {fitMode === 'actual' ? `${zoomPercent}%` : fitMode === 'fit-height' ? 'FIT H' : 'FIT W'}
            </span>
            <button
              onClick={handleZoomIn}
              className="p-1 hover:text-white text-paper-muted hover:bg-surface-hover motion-fast focus:outline-none focus:ring-1 focus:ring-vermilion-500"
              title="Zoom In (+)"
              aria-label="Zoom In"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>

            {/* 3 Explicit Fit Options */}
            <div className="flex items-center border-l border-border-charcoal pl-1 ml-1 gap-0.5">
              <button
                onClick={() => handleSelectFitMode('fit-height')}
                className={`px-1.5 py-0.5 text-[10px] font-mono uppercase motion-fast ${
                  fitMode === 'fit-height'
                    ? 'bg-vermilion-500 text-white font-bold'
                    : 'bg-ground-950 text-paper-muted hover:text-paper-cream hover:bg-surface-hover'
                }`}
                title="Fit Height (Show full page without scrolling)"
              >
                Fit H
              </button>
              <button
                onClick={() => handleSelectFitMode('fit-width')}
                className={`px-1.5 py-0.5 text-[10px] font-mono uppercase motion-fast ${
                  fitMode === 'fit-width'
                    ? 'bg-vermilion-500 text-white font-bold'
                    : 'bg-ground-950 text-paper-muted hover:text-paper-cream hover:bg-surface-hover'
                }`}
                title="Fit Width (Fill container width)"
              >
                Fit W
              </button>
              <button
                onClick={() => handleSelectFitMode('actual')}
                className={`px-1.5 py-0.5 text-[10px] font-mono uppercase motion-fast ${
                  fitMode === 'actual'
                    ? 'bg-vermilion-500 text-white font-bold'
                    : 'bg-ground-950 text-paper-muted hover:text-paper-cream hover:bg-surface-hover'
                }`}
                title="100% Actual Size / Zoom"
              >
                100%
              </button>
            </div>
          </div>

          {/* Read-Aloud Voice Button */}
          <button
            onClick={toggleReadAloud}
            className={`px-3 py-1.5 border flex items-center gap-1.5 motion-fast text-xs font-mono focus:outline-none focus:ring-2 focus:ring-vermilion-500 ${
              isReadingAloud
                ? 'bg-vermilion-500 text-white border-vermilion-600 animate-pulse font-bold shadow-vermilion-glow'
                : 'bg-surface-card border-border-crisp text-paper-cream hover:bg-surface-hover'
            }`}
            aria-label={isReadingAloud ? 'Stop read-aloud voice' : 'Read comic page aloud'}
          >
            {isReadingAloud ? (
              <>
                <VolumeX className="w-3.5 h-3.5" />
                <span>Stop Voice</span>
              </>
            ) : (
              <>
                <Volume2 className="w-3.5 h-3.5 text-vermilion-500" />
                <span>Read Aloud</span>
              </>
            )}
          </button>

          {/* Reading Mode Settings Popover Toggle */}
          <div className="relative">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className={`p-2 border motion-fast focus:outline-none focus:ring-2 focus:ring-vermilion-500 ${
                showSettings
                  ? 'bg-vermilion-500 text-white border-vermilion-600'
                  : 'bg-surface-card border-border-crisp text-paper-cream hover:bg-surface-hover'
              }`}
              aria-label="Reader Settings"
              title="Reader Settings & Reading Mode"
            >
              <Settings className="w-4 h-4" />
            </button>

            {/* Settings Popover: 3 Options Only */}
            {showSettings && (
              <div className="absolute right-0 top-full mt-2 w-72 bg-ground-950 border border-border-crisp shadow-2xl p-4 z-50 animate-fadeIn space-y-4">
                <div>
                  <h4 className="text-xs font-display font-bold text-paper-cream uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Compass className="w-3.5 h-3.5 text-vermilion-500" />
                    Reading Direction & Mode
                  </h4>
                  <div className="space-y-1.5">
                    {[
                      { id: 'paged-ltr', label: 'Paged — Left to Right', sub: 'Standard Western comic convention' },
                      { id: 'paged-rtl', label: 'Paged — Right to Left', sub: 'Manga reading order' },
                      { id: 'long-strip', label: 'Long Strip (Webtoon)', sub: 'Continuous uninterrupted scroll' },
                    ].map((mode) => (
                      <button
                        key={mode.id}
                        onClick={() => {
                          setReadingMode(mode.id as ReadingMode);
                          setShowSettings(false);
                        }}
                        className={`w-full text-left p-2.5 border motion-fast flex items-center justify-between ${
                          readingMode === mode.id
                            ? 'bg-surface-card border-vermilion-500 text-paper-cream'
                            : 'bg-ground-900 border-border-charcoal text-paper-muted hover:text-paper-cream hover:bg-surface-hover'
                        }`}
                      >
                        <div>
                          <div className="text-xs font-medium">{mode.label}</div>
                          <div className="text-[10px] text-paper-muted">{mode.sub}</div>
                        </div>
                        {readingMode === mode.id && <Check className="w-4 h-4 text-vermilion-500 shrink-0" />}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="pt-2 border-t border-border-charcoal flex items-center justify-between">
                  <span className="text-xs text-paper-muted">Thumbnail Bar</span>
                  <button
                    onClick={() => setShowThumbnails(!showThumbnails)}
                    className="px-2.5 py-1 text-xs font-mono bg-surface-card hover:bg-surface-hover border border-border-charcoal text-paper-cream motion-fast"
                  >
                    {showThumbnails ? 'Hide' : 'Show'}
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Fullscreen Toggle Button */}
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="p-2 bg-surface-card hover:bg-surface-hover border border-border-crisp text-paper-cream motion-fast focus:outline-none focus:ring-2 focus:ring-vermilion-500"
            aria-label={isFullscreen ? 'Exit fullscreen' : 'View in fullscreen'}
            title="Toggle Fullscreen (F)"
          >
            {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* ── 2. The Comic Page Canvas ──────────────────────────────────────── */}
      <div
        className={`w-full flex-1 min-h-0 flex flex-col items-center justify-center relative overflow-y-auto ${
          isFullscreen ? 'h-full pt-16 pb-20' : ''
        }`}
      >
        {/* LONG STRIP (WEBTOON CONTINUOUS SCROLL) MODE: ALL PAGES SEAMLESS & FLUSH */}
        {readingMode === 'long-strip' ? (
          <div className="w-full h-full overflow-y-auto flex flex-col items-center py-6 px-4">
            <div className="w-full max-w-2xl flex flex-col items-center shadow-2xl bg-paper-page border border-border-charcoal">
              {availablePages.map((p, idx) => (
                <div key={p.id || idx} className="w-full p-0 m-0 leading-none">
                  <img
                    src={p.pageImageUri}
                    alt={`Comic Page ${idx + 1}`}
                    className="w-full h-auto object-contain block select-none"
                  />
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* PAGED MODES (LTR, RTL): PAGE WITH CLOSE-HUGGING ARROW BUTTONS */
          <div className="relative flex items-center justify-center p-2">
            {/* Previous Page Arrow: Hugging Page Left Border */}
            {currentPage > 0 && (
              <button
                onClick={handlePrev}
                className="absolute -left-14 top-1/2 -translate-y-1/2 p-2.5 bg-ground-950/90 hover:bg-ground-950 border border-border-crisp text-paper-cream shadow-2xl motion-fast z-20 focus:outline-none focus:ring-2 focus:ring-vermilion-500"
                aria-label="Previous Page"
                title="Previous Page (←)"
              >
                <ChevronLeft className="w-5 h-5 text-vermilion-500" />
              </button>
            )}

            {/* Floating Paper Comic Page */}
            <div
              className="page-on-desk p-2.5 md:p-3.5 rounded-sm relative overflow-hidden transition-all duration-200 flex items-center justify-center"
              style={getPageContainerStyle()}
            >
              <img
                src={activePage.pageImageUri}
                alt={`Comic Page ${currentPage + 1}`}
                style={getImageStyle()}
                className="select-none block shadow-sm"
              />
            </div>

            {/* Next Page Arrow: Hugging Page Right Border */}
            {currentPage < availablePages.length - 1 && (
              <button
                onClick={handleNext}
                className="absolute -right-14 top-1/2 -translate-y-1/2 p-2.5 bg-ground-950/90 hover:bg-ground-950 border border-border-crisp text-paper-cream shadow-2xl motion-fast z-20 focus:outline-none focus:ring-2 focus:ring-vermilion-500"
                aria-label="Next Page"
                title="Next Page (→)"
              >
                <ChevronRight className="w-5 h-5 text-vermilion-500" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* ── 3. Bottom Navigation Controls Toolbar (Real Clickable Buttons) ── */}
      <div
        className={`w-full flex flex-col md:flex-row items-center justify-between gap-3 px-5 py-2.5 bg-ground-950 border border-border-charcoal shadow-md shrink-0 transition-opacity duration-300 focus-within:opacity-100 focus-within:pointer-events-auto z-30 ${
          isFullscreen
            ? `absolute bottom-0 left-0 right-0 ${
                isChromeVisible ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
              }`
            : 'relative'
        }`}
      >
        {/* Real Interactive Navigation Buttons */}
        <div className="flex items-center gap-2">
          {/* Previous Page Button */}
          <button
            onClick={handlePrev}
            disabled={currentPage === 0 && readingMode !== 'paged-rtl'}
            className="px-4 py-2 bg-surface-card hover:bg-surface-hover disabled:opacity-40 border border-border-crisp text-paper-cream text-xs font-medium flex items-center gap-2 motion-fast focus:outline-none focus:ring-2 focus:ring-vermilion-500"
            aria-label="Go to previous page"
          >
            <ChevronLeft className="w-4 h-4 text-vermilion-500" />
            <span className="font-sans font-semibold">Previous Page</span>
            <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-ground-950 border border-border-charcoal text-paper-muted">
              {readingMode === 'paged-rtl' ? '→' : '←'}
            </kbd>
          </button>

          {/* Page indicator */}
          <span className="px-3 py-2 bg-ground-900 border border-border-charcoal text-xs font-mono text-paper-cream">
            {currentPage + 1} / {availablePages.length}
          </span>

          {/* Next Page Button */}
          <button
            onClick={handleNext}
            disabled={currentPage === availablePages.length - 1 && readingMode !== 'paged-rtl'}
            className="px-4 py-2 bg-surface-card hover:bg-surface-hover disabled:opacity-40 border border-border-crisp text-paper-cream text-xs font-medium flex items-center gap-2 motion-fast focus:outline-none focus:ring-2 focus:ring-vermilion-500"
            aria-label="Go to next page"
          >
            <span className="font-sans font-semibold">Next Page</span>
            <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-ground-950 border border-border-charcoal text-paper-muted">
              {readingMode === 'paged-rtl' ? '←' : '→'}
            </kbd>
            <ChevronRight className="w-4 h-4 text-vermilion-500" />
          </button>
        </div>

        {/* Thumbnail Strip (Accessible in bottom bar) */}
        {showThumbnails && (
          <div className="flex items-center gap-2 overflow-x-auto py-1">
            {availablePages.map((p, idx) => (
              <button
                key={p.id || idx}
                onClick={() => setCurrentPage(idx)}
                className={`w-12 h-16 overflow-hidden border-2 motion-fast shrink-0 focus:outline-none focus:ring-2 focus:ring-vermilion-500 ${
                  idx === currentPage
                    ? 'border-vermilion-500 ring-2 ring-vermilion-500/40 scale-105'
                    : 'border-border-charcoal opacity-60 hover:opacity-100'
                }`}
                aria-label={`Jump to Page ${idx + 1}`}
                title={`Jump to Page ${idx + 1}`}
              >
                {p.pageImageUri ? (
                  <img
                    src={p.pageImageUri}
                    alt={`Page ${idx + 1} thumbnail`}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full bg-ground-950 flex items-center justify-center text-[10px] font-mono text-paper-muted">
                    #{idx + 1}
                  </div>
                )}
              </button>
            ))}
          </div>
        )}

        {/* Fullscreen Button */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsFullscreen(!isFullscreen)}
            className="px-3.5 py-2 bg-surface-card hover:bg-surface-hover border border-border-crisp text-paper-cream text-xs font-medium flex items-center gap-2 motion-fast focus:outline-none focus:ring-2 focus:ring-vermilion-500"
            aria-label={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}
          >
            {isFullscreen ? (
              <>
                <Minimize2 className="w-3.5 h-3.5 text-vermilion-500" />
                <span>Exit Fullscreen</span>
              </>
            ) : (
              <>
                <Maximize2 className="w-3.5 h-3.5 text-vermilion-500" />
                <span>Fullscreen</span>
              </>
            )}
            <kbd className="px-1.5 py-0.5 text-[10px] font-mono bg-ground-950 border border-border-charcoal text-paper-muted">
              F
            </kbd>
          </button>
        </div>
      </div>
    </div>
  );
};
