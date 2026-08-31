import { useState, useEffect, useCallback, useRef } from 'react';
import { db } from '../lib/firebase';
import { doc, onSnapshot, collection, query, orderBy } from 'firebase/firestore';

export interface Character {
  id: string;
  name: string;
  role: string;
  description: string;
  canonicalPromptFragment?: string;
  referenceSheetUris: string[];
  approved: boolean;
}

export interface DialogueLine {
  speaker?: string;
  text: string;
  bubbleType: 'speech' | 'thought' | 'caption';
}

export interface Panel {
  id: string;
  pageIndex: number;
  order: number;
  shotType: string;
  staging: string;
  charactersPresent: string[];
  action: string;
  caption: string;
  dialogue: DialogueLine[];
  draftUri?: string;
  artUri?: string;
  letteredUri?: string;
  promptHash?: string;
  status: 'pending' | 'drafted' | 'generated' | 'approved' | 'needs_review' | 'failed' | 'skipped_capped';
  criticIterations: number;
  criticNotes: string[];
}

export interface Page {
  id: string;
  index: number;
  layoutTemplate: string;
  panelIds: string[];
  pageImageUri?: string;
  status: string;
}

export interface Message {
  id: string;
  role: 'user' | 'agent';
  text: string;
  ts?: any;
}

export interface TraceEntry {
  id: string;
  ts?: any;
  stage: string;
  level: 'info' | 'decision' | 'warn';
  message: string;
  data?: any;
}

export interface CostEntry {
  id: string;
  model: string;
  mode: string;
  kind: 'image' | 'video';
  estCostUsd: number;
  panelId?: string;
  ts?: any;
}

export interface ProjectData {
  id: string;
  status: 'intake' | 'designing' | 'planning' | 'drawing' | 'lettering' | 'laying_out' | 'exporting' | 'done' | 'capped' | 'error';
  progress: number;
  title: string;
  logline: string;
  options: {
    style: string;
    pageCount: number;
    rating: string;
    aspect: string;
    palette: string;
    pacing: string;
  };
  costMode: 'DEV' | 'PREVIEW' | 'FINAL';
  imagesGenerated: number;
  estSpendUsd: number;
  result?: {
    readerManifestUri?: string;
    pdfUri?: string;
    bibleJsonUri?: string;
    motionUri?: string;
  };
  createdAt?: any;
  updatedAt?: any;
  error?: string;
  characters: Character[];
  panels: Panel[];
  pages: Page[];
  messages: Message[];
  traces: TraceEntry[];
  costs: CostEntry[];
}

export function useProject(projectId: string | null) {
  const [project, setProject] = useState<ProjectData | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const pollingTimerRef = useRef<number | null>(null);

  const fetchProjectHttp = useCallback(async (pid: string) => {
    try {
      const res = await fetch(`/projects/${pid}`);
      if (!res.ok) throw new Error(`HTTP error: ${res.status}`);
      const data = await res.json();
      setProject(data);
      return data;
    } catch (err: any) {
      console.error('[useProject] Polling error:', err);
      setError(err.message || 'Failed to fetch project');
      return null;
    }
  }, []);

  // Main listener / polling effect
  useEffect(() => {
    if (!projectId) {
      setProject(null);
      return;
    }

    setLoading(true);
    let unsubProject: (() => void) | null = null;
    let unsubMessages: (() => void) | null = null;
    let unsubTraces: (() => void) | null = null;
    let unsubPanels: (() => void) | null = null;
    let unsubCharacters: (() => void) | null = null;
    let unsubPages: (() => void) | null = null;

    if (db) {
      // ── Realtime Firebase Mode ──────────────────────────────────────────
      try {
        const projRef = doc(db, 'projects', projectId);
        unsubProject = onSnapshot(projRef, (snap) => {
          if (snap.exists()) {
            const data = snap.data();
            setProject((prev) => ({
              ...(prev || ({} as ProjectData)),
              ...data,
              id: snap.id,
              characters: prev?.characters || [],
              panels: prev?.panels || [],
              pages: prev?.pages || [],
              messages: prev?.messages || [],
              traces: prev?.traces || [],
              costs: prev?.costs || [],
            } as ProjectData));
            setLoading(false);
          }
        });

        // Messages subcollection
        const msgQuery = query(collection(db, 'projects', projectId, 'messages'), orderBy('ts', 'asc'));
        unsubMessages = onSnapshot(msgQuery, (snap) => {
          const msgs = snap.docs.map((d) => ({ id: d.id, ...d.data() } as Message));
          setProject((prev) => prev ? { ...prev, messages: msgs } : null);
        });

        // Traces subcollection
        const traceQuery = query(collection(db, 'projects', projectId, 'traces'), orderBy('ts', 'asc'));
        unsubTraces = onSnapshot(traceQuery, (snap) => {
          const trs = snap.docs.map((d) => ({ id: d.id, ...d.data() } as TraceEntry));
          setProject((prev) => prev ? { ...prev, traces: trs } : null);
        });

        // Panels subcollection
        unsubPanels = onSnapshot(collection(db, 'projects', projectId, 'panels'), (snap) => {
          const pns = snap.docs.map((d) => ({ id: d.id, ...d.data() } as Panel));
          pns.sort((a, b) => (a.pageIndex !== b.pageIndex ? a.pageIndex - b.pageIndex : a.order - b.order));
          setProject((prev) => prev ? { ...prev, panels: pns } : null);
        });

        // Characters subcollection
        unsubCharacters = onSnapshot(collection(db, 'projects', projectId, 'characters'), (snap) => {
          const chars = snap.docs.map((d) => ({ id: d.id, ...d.data() } as Character));
          setProject((prev) => prev ? { ...prev, characters: chars } : null);
        });

        // Pages subcollection
        unsubPages = onSnapshot(collection(db, 'projects', projectId, 'pages'), (snap) => {
          const pgs = snap.docs.map((d) => ({ id: d.id, ...d.data() } as Page));
          pgs.sort((a, b) => a.index - b.index);
          setProject((prev) => prev ? { ...prev, pages: pgs } : null);
        });
      } catch (err) {
        console.warn('[useProject] Realtime listener error; falling back to polling:', err);
      }
    }

    // ── HTTP Polling Fallback ───────────────────────────────────────────────
    fetchProjectHttp(projectId)
      .catch(() => {
        // Provide mock fallback data if backend is offline
        setProject((prev) => {
          if (prev && prev.id === projectId) return prev;
          return {
            id: projectId,
            status: 'intake',
            progress: 10,
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
            messages: [
              {
                id: 'm1',
                role: 'user',
                text: 'An old lighthouse keeper named Elara discovers the light seals an ancient dark creature beneath the waves. During a catastrophic storm, the light fails, and she has one night to fix it before the creature rises.',
                ts: Date.now() - 10000,
              },
              {
                id: 'm2',
                role: 'agent',
                text: 'I have extracted your core premise: an ancient lighthouse keeper battling a stormy leviathan. Before we design the character reference sheets and layout panels:\n\n1. Should Elara have a weathered classic maritime aesthetic or an arcane-steampunk outfit?\n2. What color palette do you prefer for the leviathan below the waves?',
                ts: Date.now() - 5000,
              },
            ],
            characters: [
              {
                id: 'c1',
                name: 'Elara Thorne',
                role: 'protagonist',
                description: 'Weathered keeper in her 60s, heavy oilskin jacket, brass storm lantern, sharp discerning gaze.',
                referenceSheetUris: [],
                approved: false,
              },
              {
                id: 'c2',
                name: 'The Abyssal Leviathan',
                role: 'antagonist',
                description: 'Colossal bioluminescent sea creature sealed in the abyssal trench below the beacon.',
                referenceSheetUris: [],
                approved: false,
              },
            ],
            panels: [],
            pages: [],
            traces: [],
            costs: [],
          };
        });
      })
      .finally(() => setLoading(false));

    const poll = async () => {
      const p = await fetchProjectHttp(projectId);
      const isActive = p && ['designing', 'planning', 'drawing', 'lettering', 'laying_out', 'exporting'].includes(p.status);
      const interval = isActive ? 1500 : 4000;
      pollingTimerRef.current = window.setTimeout(poll, interval);
    };

    pollingTimerRef.current = window.setTimeout(poll, 3000);

    return () => {
      if (unsubProject) unsubProject();
      if (unsubMessages) unsubMessages();
      if (unsubTraces) unsubTraces();
      if (unsubPanels) unsubPanels();
      if (unsubCharacters) unsubCharacters();
      if (unsubPages) unsubPages();
      if (pollingTimerRef.current) clearTimeout(pollingTimerRef.current);
    };
  }, [projectId, fetchProjectHttp]);

  // Actions
  const sendTurn = async (text: string) => {
    if (!projectId) return;
    try {
      const res = await fetch(`/projects/${projectId}/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });
      if (!res.ok) throw new Error(`Turn failed: ${res.status}`);
      await fetchProjectHttp(projectId);
    } catch (err: any) {
      console.warn('[sendTurn] Backend unreachable, adding mock conversation turn:', err);
      setProject((prev) => {
        if (!prev) return null;
        const newMsgs: Message[] = [
          ...(prev.messages || []),
          { id: 'usr_' + Date.now(), role: 'user', text, ts: Date.now() },
          {
            id: 'agt_' + (Date.now() + 100),
            role: 'agent',
            text: `Understood! I have locked that direction. Character descriptions are synchronized and we are ready to generate the 6-page comic pipeline.`,
            ts: Date.now() + 100,
          },
        ];
        return { ...prev, messages: newMsgs, status: 'designing' };
      });
    }
  };

  const approveItem = async (target: 'character' | 'panel', id: string, decision: 'approve' | 'reject', note = '') => {
    if (!projectId) return;
    try {
      const res = await fetch(`/projects/${projectId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ target, id, decision, note }),
      });
      if (!res.ok) throw new Error(`Approve failed: ${res.status}`);
      await fetchProjectHttp(projectId);
    } catch (err: any) {
      console.error('[approveItem] error:', err);
      setError(err.message);
    }
  };

  const triggerGeneration = async () => {
    if (!projectId) return;
    try {
      const res = await fetch(`/worker/trigger/${projectId}`, { method: 'POST' });
      if (!res.ok) {
        console.log('Worker trigger endpoint returned', res.status);
      }
      await fetchProjectHttp(projectId);
    } catch (err: any) {
      console.error('[triggerGeneration] error:', err);
    }
  };

  const createProject = async (story?: string, title?: string): Promise<string | null> => {
    try {
      setLoading(true);
      const res = await fetch('/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title || (story ? story.slice(0, 40) + '...' : 'New Comic'),
          story: story || undefined,
        }),
      });
      if (!res.ok) throw new Error(`Project creation failed: ${res.status}`);
      const data = await res.json();
      return data.projectId;
    } catch (err: any) {
      console.warn('[createProject] Backend unreachable, creating local project:', err);
      const mockId = 'proj_' + Math.random().toString(36).substring(2, 9);
      const mockProject: ProjectData = {
        id: mockId,
        status: 'intake',
        progress: 10,
        title: title || (story ? story.slice(0, 32) + '...' : 'The Last Lighthouse Keeper'),
        logline: story ? story.slice(0, 140) + '...' : 'An ancient keeper discovers the lighthouse beam seals a dark leviathan in the ocean depths.',
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
        messages: [
          ...(story ? [{ id: 'm1', role: 'user' as const, text: story, ts: Date.now() - 2000 }] : []),
          {
            id: 'm2',
            role: 'agent' as const,
            text: 'I have extracted your core premise: an ancient lighthouse keeper battling a stormy leviathan. Before we design the character reference sheets and layout panels:\n\n1. Should Elara have a weathered classic maritime aesthetic or an arcane-steampunk outfit?\n2. What color palette do you prefer for the leviathan below the waves?',
            ts: Date.now(),
          },
        ],
        characters: [
          {
            id: 'c1',
            name: 'Elara Thorne',
            role: 'protagonist',
            description: 'Weathered keeper in her 60s, oilskin jacket, lantern, sharp discerning gaze.',
            referenceSheetUris: [],
            approved: false,
          },
          {
            id: 'c2',
            name: 'The Abyssal Leviathan',
            role: 'antagonist',
            description: 'Colossal bioluminescent sea creature sealed in the abyssal trench below the beacon.',
            referenceSheetUris: [],
            approved: false,
          },
        ],
        panels: [],
        pages: [],
        traces: [],
        costs: [],
      };
      setProject(mockProject);
      return mockId;
    } finally {
      setLoading(false);
    }
  };

  return {
    project,
    loading,
    error,
    createProject,
    sendTurn,
    approveItem,
    triggerGeneration,
    refresh: () => projectId && fetchProjectHttp(projectId),
  };
}
