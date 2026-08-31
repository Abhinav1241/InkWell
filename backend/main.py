"""
Inkwell — FastAPI Application

Routes:
  GET  /healthz                         → health check
  POST /projects                        → create project
  POST /projects/{id}/turn              → intake chat turn
  POST /projects/{id}/approve           → approve/reject character or panel
  GET  /projects/{id}                   → get project state
  POST /assets/upload-url               → signed GCS upload URL
  POST /worker/trigger/{id}             → LOCAL DEV ONLY: trigger worker inline
  POST /pubsub/push                     → Pub/Sub push handler for worker

Single Cloud Run service: serves API + static frontend (when built).
"""

from __future__ import annotations

import base64
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.cloud import firestore  # type: ignore[import-untyped]

from backend import config
from backend.models.schemas import (
    ApproveRequest,
    CreateProjectRequest,
    TurnRequest,
)
from backend.tools import gemini_text

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="Inkwell", version="0.1.0")

# CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Firestore client ────────────────────────────────────────────────────────

_db: firestore.Client | None = None


def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=config.PROJECT_ID or None)
    return _db


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Health ──────────────────────────────────────────────────────────────────

@app.get("/healthz")
def healthz():
    return {"status": "ok", "costMode": config.COST_MODE}


# ── Projects ────────────────────────────────────────────────────────────────

@app.post("/projects")
async def create_project(req: CreateProjectRequest):
    """Create a new comic project. If story text is provided, run intake."""
    db = _get_db()
    project_id = uuid.uuid4().hex[:12]
    now = _now()

    project_data: dict[str, Any] = {
        "status": "intake",
        "progress": 0,
        "title": req.title or "",
        "logline": "",
        "options": {
            "style": "manga-influenced modern comic",
            "pageCount": config.DEFAULT_PAGES,
            "rating": "all-ages",
            "aspect": "3:4",
            "palette": "vibrant",
            "pacing": "balanced",
        },
        "costMode": config.COST_MODE,
        "imagesGenerated": 0,
        "estSpendUsd": 0.0,
        "result": None,
        "createdAt": now,
        "updatedAt": now,
        "error": None,
    }

    db.collection("projects").document(project_id).set(project_data)

    # If story text provided, run intake extraction
    bible: dict[str, Any] | None = None
    agent_reply = "Tell me your story! Paste your script, rough notes, or even just a paragraph describing what you want."

    if req.story:
        # Save user message
        db.collection("projects").document(project_id)\
          .collection("messages").add({
              "role": "user",
              "text": req.story,
              "ts": now,
          })

        try:
            extraction = gemini_text.extract_story(req.story)
            bible = {
                "premise": extraction.get("logline", ""),
                "tone": extraction.get("tone", ""),
                "setting": extraction.get("setting", ""),
            }

            # Save characters
            for char_data in extraction.get("characters", []):
                char_id = uuid.uuid4().hex[:8]
                db.collection("projects").document(project_id)\
                  .collection("characters").document(char_id).set({
                      "name": char_data.get("name", "Unknown"),
                      "role": char_data.get("role", "supporting"),
                      "description": char_data.get("description", ""),
                      "canonicalPromptFragment": char_data.get("description", ""),
                      "referenceSheetUris": [],
                      "traits": {},
                      "approved": False,
                      "firstAppearancePage": 0,
                  })

            # Save primary location/setting
            setting = extraction.get("setting", "")
            if setting:
                loc_id = f"loc_{uuid.uuid4().hex[:8]}"
                loc_name = setting.split(",")[0].strip()
                if len(loc_name) > 40:
                    loc_name = "Primary Setting"
                db.collection("projects").document(project_id)\
                  .collection("locations").document(loc_id).set({
                      "name": loc_name,
                      "description": setting,
                      "canonicalPromptFragment": setting,
                      "referenceSheetUris": [],
                      "approved": True,
                  })

            # Save bible
            db.collection("projects").document(project_id)\
              .collection("bible").document("core").set(bible)

            # Update project
            db.collection("projects").document(project_id).update({
                "title": req.title or extraction.get("logline", "")[:60],
                "logline": extraction.get("logline", ""),
                "updatedAt": _now(),
            })

            # Build reply with clarifying questions
            questions = extraction.get("questions", [])
            if questions:
                agent_reply = "Great story! I have a few questions to lock the creative direction:\n\n"
                for i, q in enumerate(questions, 1):
                    agent_reply += f"{i}. {q}\n"
            else:
                agent_reply = f"Got it — \"{extraction.get('logline', '')}\"! Ready to start designing characters."

        except Exception as e:
            log.error("Intake extraction failed: %s", e)
            agent_reply = f"I got your story! Let me ask some clarifying questions to get the direction right. Could you tell me more about the art style and tone you're envisioning?"

        # Save agent reply
        db.collection("projects").document(project_id)\
          .collection("messages").add({
              "role": "agent",
              "text": agent_reply,
              "ts": _now(),
          })

    return {
        "projectId": project_id,
        "status": "intake",
        "agentReply": agent_reply,
        "bible": bible,
    }


@app.post("/projects/{project_id}/turn")
async def turn(project_id: str, req: TurnRequest):
    """Handle a chat turn: user answers → update bible → reply."""
    db = _get_db()
    proj = db.collection("projects").document(project_id).get()
    if not proj.exists:
        raise HTTPException(404, "Project not found")

    now = _now()

    # Save user message
    db.collection("projects").document(project_id)\
      .collection("messages").add({
          "role": "user",
          "text": req.text,
          "ts": now,
      })

    # Get current bible
    bible_doc = db.collection("projects").document(project_id)\
                  .collection("bible").document("core").get()
    bible = bible_doc.to_dict() if bible_doc.exists else {}

    # Apply user's answers to the bible
    try:
        updated_bible = gemini_text.apply_answers(bible, {"user_input": req.text})
        db.collection("projects").document(project_id)\
          .collection("bible").document("core").set(updated_bible)
        bible = updated_bible
    except Exception as e:
        log.warning("Failed to apply answers: %s", e)

    # Determine reply
    agent_reply = (
        "Direction locked! Your characters, style, and story are set. "
        "Ready to start designing character reference sheets and planning panels. "
        "Trigger generation when you're ready."
    )

    # Update project status
    db.collection("projects").document(project_id).update({
        "status": "designing",
        "updatedAt": _now(),
    })

    # Save agent reply
    db.collection("projects").document(project_id)\
      .collection("messages").add({
          "role": "agent",
          "text": agent_reply,
          "ts": _now(),
      })

    return {
        "agentReply": agent_reply,
        "bible": bible,
        "status": "designing",
    }


@app.post("/projects/{project_id}/approve")
async def approve(project_id: str, req: ApproveRequest):
    """Approve or reject a character sheet or panel."""
    db = _get_db()
    proj = db.collection("projects").document(project_id).get()
    if not proj.exists:
        raise HTTPException(404, "Project not found")

    if req.target == "character":
        char_ref = db.collection("projects").document(project_id)\
                     .collection("characters").document(req.id)
        char_doc = char_ref.get()
        if not char_doc.exists:
            raise HTTPException(404, "Character not found")

        if req.decision == "approve":
            char_ref.update({"approved": True})
            return {"status": "approved", "charId": req.id}
        else:
            char_ref.update({"approved": False})
            # Note is stored for regeneration context
            return {"status": "rejected", "charId": req.id, "note": req.note}

    elif req.target == "location":
        loc_ref = db.collection("projects").document(project_id)\
                    .collection("locations").document(req.id)
        loc_doc = loc_ref.get()
        if not loc_doc.exists:
            raise HTTPException(404, "Location not found")

        if req.decision == "approve":
            loc_ref.update({"approved": True})
            return {"status": "approved", "locId": req.id}
        else:
            loc_ref.update({"approved": False})
            return {"status": "rejected", "locId": req.id, "note": req.note}

    elif req.target == "panel":
        panel_ref = db.collection("projects").document(project_id)\
                      .collection("panels").document(req.id)
        panel_doc = panel_ref.get()
        if not panel_doc.exists:
            raise HTTPException(404, "Panel not found")

        if req.decision == "approve":
            panel_ref.update({"status": "approved"})
            return {"status": "approved", "panelId": req.id}
        else:
            panel_ref.update({"status": "pending"})
            return {"status": "rejected", "panelId": req.id, "note": req.note}

    raise HTTPException(400, f"Unknown target: {req.target}")


@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Get full project state including characters, locations, pages, panels."""
    db = _get_db()
    proj = db.collection("projects").document(project_id).get()
    if not proj.exists:
        raise HTTPException(404, "Project not found")

    data = proj.to_dict()

    # Fetch subcollections
    characters = []
    for doc in db.collection("projects").document(project_id)\
                 .collection("characters").stream():
        char = doc.to_dict()
        char["id"] = doc.id
        characters.append(char)

    locations = []
    for doc in db.collection("projects").document(project_id)\
                 .collection("locations").stream():
        loc = doc.to_dict()
        loc["id"] = doc.id
        locations.append(loc)

    panels = []
    for doc in db.collection("projects").document(project_id)\
                 .collection("panels").stream():
        panel = doc.to_dict()
        panel["id"] = doc.id
        panels.append(panel)

    pages = []
    for doc in db.collection("projects").document(project_id)\
                 .collection("pages").stream():
        page = doc.to_dict()
        page["id"] = doc.id
        pages.append(page)

    messages = []
    for doc in db.collection("projects").document(project_id)\
                 .collection("messages").order_by("ts").stream():
        msg = doc.to_dict()
        msg["id"] = doc.id
        messages.append(msg)

    traces = []
    for doc in db.collection("projects").document(project_id)\
                 .collection("traces").order_by("ts").limit(50).stream():
        t = doc.to_dict()
        t["id"] = doc.id
        traces.append(t)

    costs = []
    for doc in db.collection("projects").document(project_id)\
                 .collection("costs").stream():
        c = doc.to_dict()
        c["id"] = doc.id
        costs.append(c)

    data["characters"] = characters
    data["locations"] = locations
    data["panels"] = sorted(panels, key=lambda p: (p.get("pageIndex", 0), p.get("order", 0)))
    data["pages"] = sorted(pages, key=lambda p: p.get("index", 0))
    data["messages"] = messages
    data["traces"] = traces
    data["costs"] = costs

    return data


@app.get("/media/{path:path}")
async def serve_media(path: str):
    """Serve media files from GCS bucket with browser caching."""
    from backend.tools import storage
    from fastapi.responses import Response
    try:
        data = storage.download_bytes(path)
        content_type = storage._content_type(path)
        return Response(
            content=data,
            media_type=content_type,
            headers={"Cache-Control": "public, max-age=86400"},
        )
    except Exception as e:
        log.warning("Media download error for %s: %s", path, e)
        raise HTTPException(404, "Media not found")


@app.post("/assets/upload-url")
async def get_upload_url(request: Request):
    """Generate a signed upload URL for direct GCS upload."""
    from backend.tools.storage import signed_upload_url
    body = await request.json()
    path = body.get("path", "")
    ct = body.get("contentType", "image/png")
    url = signed_upload_url(path, content_type=ct)
    return {"uploadUrl": url}


# ── Worker Pipeline Trigger ──────────────────────────────────────────────────

@app.post("/worker/trigger/{project_id}")
async def trigger_worker(project_id: str):
    """Trigger the worker pipeline asynchronously in the background."""
    import asyncio
    from backend.worker import run_pipeline

    db = _get_db()
    proj = db.collection("projects").document(project_id).get()
    if not proj.exists:
        raise HTTPException(404, "Project not found")

    # Launch background task
    asyncio.create_task(run_pipeline(project_id))
    log.info("Launched background comic studio pipeline for project %s", project_id)

    return {"status": "queued", "projectId": project_id}


# ── Pub/Sub Push Handler ────────────────────────────────────────────────────

@app.post("/pubsub/push")
async def pubsub_push(request: Request):
    """Handle Pub/Sub push messages for background generation asynchronously."""
    import asyncio
    body = await request.json()
    message = body.get("message", {})
    data_b64 = message.get("data", "")

    if data_b64:
        payload = json.loads(base64.b64decode(data_b64))
        project_id = payload.get("projectId")
        if project_id:
            from backend.worker import run_pipeline
            # Launch in background and acknowledge immediately to avoid Cloud Run request timeouts
            asyncio.create_task(run_pipeline(project_id))
            log.info("Pub/Sub triggered background pipeline for project %s", project_id)

    return {"status": "ok"}


# ── Static frontend (production) ────────────────────────────────────────────

_frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
_frontend_index = os.path.join(_frontend_dist, "index.html")

if os.path.isdir(_frontend_dist):
    _app_assets = os.path.join(_frontend_dist, "app-assets")
    if os.path.isdir(_app_assets):
        app.mount("/app-assets", StaticFiles(directory=_app_assets), name="app-assets")
    _assets = os.path.join(_frontend_dist, "assets")
    if os.path.isdir(_assets):
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(_frontend_dist, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        if os.path.isfile(_frontend_index):
            return FileResponse(_frontend_index)
        raise HTTPException(404, "Frontend build not found")
