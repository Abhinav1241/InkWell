"""
Inkwell — Panel Planner Agent (§8.2)

Gemini 3.5 Flash specialist that turns the Story Bible into a structured
page/panel breakdown with shot types, staging, pacing, and dialogue placement.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from google.cloud import firestore  # type: ignore[import-untyped]

from backend import config
from backend.agents.bible_manager import BibleManager
from backend.telemetry import trace_event
from backend.tools import gemini_text

log = logging.getLogger(__name__)

_db: firestore.Client | None = None


def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=config.PROJECT_ID or None)
    return _db


class PanelPlannerAgent:
    """Specialist agent decomposing stories into pages and panel plans."""

    def __init__(self, project_id: str, db_client: firestore.Client | None = None):
        self.project_id = project_id
        self._db = db_client or _get_db()
        self.bible_manager = BibleManager(project_id, self._db)

    def plan_comic(self, options: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Generate structured panel plan and persist pages & panels to Firestore.

        Returns (pages_list, panels_list).
        """
        trace_event(self.project_id, "panel_planning", "info", "Decomposing story into pages & panels...")

        bible = self.bible_manager.get_core_bible()
        target_page_count = int(options.get("pageCount") or options.get("page_count") or config.DEFAULT_PAGES)
        plan = gemini_text.plan_panels(bible, options)

        pages = plan.get("pages", [])
        if len(pages) > target_page_count:
            log.warning(
                "PanelPlannerAgent: LLM produced %d pages; hard clamping to target_page_count=%d",
                len(pages),
                target_page_count,
            )
            pages = pages[:target_page_count]

        all_panels = []
        all_pages = []

        proj_ref = self._db.collection("projects").document(self.project_id)

        for p_idx, page_data in enumerate(pages):
            page_id = uuid.uuid4().hex[:8]
            panel_ids = []

            for panel_order, p_data in enumerate(page_data.get("panels", [])):
                panel_id = uuid.uuid4().hex[:8]
                panel_ids.append(panel_id)

                dialogue = [
                    {
                        "speaker": d.get("speaker"),
                        "text": d.get("text", ""),
                        "bubbleType": d.get("bubbleType", "speech"),
                    }
                    for d in p_data.get("dialogue", [])
                ]

                panel_doc = {
                    "id": panel_id,
                    "pageIndex": p_idx,
                    "order": panel_order,
                    "shotType": p_data.get("shotType", "medium"),
                    "staging": p_data.get("staging", ""),
                    "charactersPresent": p_data.get("charactersPresent", []),
                    "action": p_data.get("action", ""),
                    "caption": p_data.get("caption", ""),
                    "dialogue": dialogue,
                    "draftUri": None,
                    "artUri": None,
                    "letteredUri": None,
                    "promptHash": None,
                    "status": "pending",
                    "criticIterations": 0,
                    "criticNotes": [],
                }

                proj_ref.collection("panels").document(panel_id).set(panel_doc)
                all_panels.append(panel_doc)

            page_doc = {
                "id": page_id,
                "index": p_idx,
                "layoutTemplate": "auto",
                "panelIds": panel_ids,
                "pageImageUri": None,
                "status": "pending",
            }
            proj_ref.collection("pages").document(page_id).set(page_doc)
            all_pages.append(page_doc)

        trace_event(
            self.project_id,
            "panel_planning",
            "decision",
            f"✓ Script breakdown complete: {len(all_pages)} pages, {len(all_panels)} total panels (target={target_page_count})",
        )
        return all_pages, all_panels
