# Inkwell Architecture

## Overview

A **single Cloud Run service** hosts both the FastAPI API and the static React frontend.
Background generation runs via Pub/Sub push messages to the same service (or inline via
a dev-only trigger endpoint for local testing). The ADK multi-agent studio is powered by
Gemini 3.5 Flash (reasoning + vision critic) and the Nano Banana image models on Vertex AI.

All state is externalized to **Firestore** (projects, Story Bible, panels, chat, traces,
cost ledger); art and exports live in **Cloud Storage**. Reasoning is emitted as
OpenTelemetry spans to **Cloud Trace** and as human-readable trace entries to Firestore.

## Architecture Diagram

```
                          ┌────────────────────────────────────────────┐
                          │                  USER                      │
                          │ (chats, approves sheets, reads the comic)  │
                          └──────────────────┬─────────────────────────┘
                                             │ HTTPS
                          ┌──────────────────▼──────────────────────┐
                          │   CLOUD RUN (single service)            │
                          │                                         │
                          │  ┌─────────────┐   ┌─────────────────┐  │
                          │  │  React SPA   │   │   FastAPI API   │  │
                          │  │  (static)    │   │  /projects      │  │
                          │  │  intake chat │   │  /turn          │  │
                          │  │  gallery     │   │  /approve       │  │
                          │  │  studio grid │   │  /pubsub/push   │  │
                          │  │  critic feed │   │  /worker/trigger│  │
                          │  │  reader      │   │  (dev only)     │  │
                          │  └─────────────┘   └──────┬──────────┘  │
                          └────────────────────────────┼────────────┘
                                                       │
                          ┌────────────────────────────▼────────────┐
                          │               Pub/Sub                   │
                          │           inkwell-jobs topic             │
                          └────────────────────────────┬────────────┘
                                                       │ push
                     ┌─────────────────────────────────▼──────────────────┐
                     │              WORKER PIPELINE (ADK)                  │
                     │                                                     │
                     │  ┌──── Orchestrator (phase control + CostGuard) ──┐ │
                     │  │                                                 │ │
                     │  │  Intake ──► Character ──► Style ──► Planner    │ │
                     │  │            Designer     Guide                   │ │
                     │  │                                                 │ │
                     │  │  For each panel:                                │ │
                     │  │    CostGuard ──► Generate ──► Critic Loop      │ │
                     │  │                   (refs)      (vision check     │ │
                     │  │                               re-draw if drift) │ │
                     │  │                                                 │ │
                     │  │  Letterer ──► Layout ──► Exporter ──► Motion   │ │
                     │  │  (Pillow)    (templates)  (PDF)      (Veo/TTS) │ │
                     │  └─────────────────────────────────────────────────┘ │
                     └──────────┬──────────────────┬───────────────────────┘
                                │                  │
              ┌─────────────────▼──┐     ┌─────────▼───────────────────┐
              │  Cloud Storage     │     │       Firestore             │
              │  characters/       │◄────┤ projects · bible ·         │
              │  panels/           │     │ characters · pages ·       │
              │  pages/            │     │ panels · messages ·        │
              │  exports/          │     │ traces · costs             │
              │  motion/           │     └─────────────────────────────┘
              └────────────────────┘
                                │
              Gemini 3.5 Flash · Nano Banana 2 · Nano Banana Pro
              Veo 3.1 · Lyria · Chirp 3 HD (Vertex AI)
```

## Components

- **Frontend** (React/static): intake chat, character gallery, studio grid, critic feed, reader
- **API** (FastAPI): project + turn endpoints, approvals, signed URLs, Pub/Sub handler
- **Worker** (ADK pipeline): Orchestrator + sub-agents
- **Agents**: Intake, CharacterDesigner, StyleGuide, PanelPlanner, PanelGenerator,
  ConsistencyCritic (vision loop), Letterer, Layout, Exporter, Motion (bonus)
- **Tools**: cost_guard (mode/caps/ledger/cache), gemini_image, gemini_vision, gemini_text,
  compositor (Pillow lettering + template layout), pdf, veo, lyria, tts, gemma, storage
- **Data**: Firestore (projects/bible/characters/pages/panels/messages/costs/traces), GCS

## Consistency Strategy

1. Approved character **reference sheets** are passed as reference inputs to every panel generation
2. Identical **canonical prompt fragment** used across all panels for each character
3. A **vision critic** verifies each character against their sheet after generation
4. On drift → **corrective re-draw** with specific notes (up to MAX_CRITIC_ITERS)
5. On exhaust → `needs_review` status (never blocks the pipeline)

## Cost Architecture

- Three cost modes (`DEV`/`PREVIEW`/`FINAL`) resolve the image model and quality
- Per-project image cap (40) acts as a circuit breaker
- Prompt-hash cache prevents redundant regeneration
- Every generation recorded in a spend ledger surfaced in the UI
- Character sheets use Pro model in FINAL mode even if panels use draft
- Veo disabled outside FINAL mode; once-per-project flag
- Re-lettering never triggers image regeneration

## Failure Tolerance

- Externalized state in Firestore (restart-safe)
- Per-panel retry-then-flag (never crashes the pipeline)
- Critic max-iteration cap with `needs_review` fallback
- Malformed-JSON retry on text model responses
- Image cap reached → `skipped_capped` status with clear trace
- Graceful degradation at every stage
