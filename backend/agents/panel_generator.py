"""
Inkwell — Panel Generator Agent (§8.2)

Draws comic panels passing character reference sheets and canonical prompt fragments
for character consistency. Checks prompt-hash cache first.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from google.cloud import firestore  # type: ignore[import-untyped]

from backend import config
from backend.agents.bible_manager import BibleManager
from backend.telemetry import trace_event
from backend.tools import cost_guard, gemini_image

log = logging.getLogger(__name__)

_db: firestore.Client | None = None


def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=config.PROJECT_ID or None)
    return _db


class PanelGeneratorAgent:
    """Specialist agent composing panel prompts with reference image consistency."""

    def __init__(self, project_id: str, db_client: firestore.Client | None = None):
        self.project_id = project_id
        self._db = db_client or _get_db()
        self.bible_manager = BibleManager(project_id, self._db)

    def draw_panel(
        self,
        panel: dict[str, Any],
        style_phrase: str,
        style_ref_uri: Optional[str] = None,
        corrective_notes: str = "",
        mode: str | None = None,
    ) -> tuple[Optional[str], Optional[str]]:
        """Generate artwork for a panel passing reference sheets for present characters.

        Returns (art_uri, prompt_hash).
        """
        panel_id = panel["id"]
        action = panel.get("action", "")

        # Check cap
        ok, reason = cost_guard.can_generate(self.project_id)
        if not ok:
            trace_event(self.project_id, "panel_generation", "warn", f"Panel {panel_id} skipped: {reason}")
            return None, None

        # Build character descriptions and collect reference sheets
        characters = self.bible_manager.list_characters()
        char_map = {c["name"]: c for c in characters}

        char_descs = []
        ref_uris = []
        for char_name in panel.get("charactersPresent", []):
            char = char_map.get(char_name, {})
            fragment = char.get("canonicalPromptFragment", char_name)
            char_descs.append(f"{char_name}: {fragment}")
            ref_uris.extend(char.get("referenceSheetUris", []))

        # Include location reference sheets
        locations = self.bible_manager.list_locations()
        for loc in locations:
            ref_uris.extend(loc.get("referenceSheetUris", []))

        if style_ref_uri:
            ref_uris.append(style_ref_uri)

        from backend.prompts.prompts import P4_PANEL_ART
        prompt = P4_PANEL_ART.format(
            style_phrase=style_phrase,
            shot_type=panel.get("shotType", "medium"),
            staging=panel.get("staging", ""),
            action=action,
            character_descriptions="\n".join(char_descs) if char_descs else "No specific characters",
        )

        if corrective_notes:
            prompt += corrective_notes

        trace_event(
            self.project_id,
            "panel_generation",
            "info",
            f"Drawing panel {panel_id} ({panel.get('shotType', 'medium')}): '{action[:50]}...'",
        )

        try:
            art_uri, phash = gemini_image.generate_panel(
                project_id=self.project_id,
                panel_id=panel_id,
                prompt=prompt,
                reference_image_uris=ref_uris,
                page_index=panel.get("pageIndex", 0),
                mode=mode,
            )

            # Persist to Firestore
            self._db.collection("projects").document(self.project_id)\
                .collection("panels").document(panel_id).update({
                    "artUri": art_uri,
                    "promptHash": phash,
                    "status": "generated",
                })

            trace_event(self.project_id, "panel_generation", "info", f"✓ Panel {panel_id} rendered")
            return art_uri, phash

        except Exception as e:
            trace_event(self.project_id, "panel_generation", "warn", f"Panel {panel_id} generation failed: {e}")
            return None, None
