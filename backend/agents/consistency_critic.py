"""
Inkwell — Consistency Critic Agent (§8.2, LoopAgent equivalent)

The multi-modal QA loop:
Evaluates generated panels with Gemini 3.5 Flash vision against:
1. Character consistency (face, hair, build, outfit) vs approved reference sheets
2. House art style match vs style guide reference
3. Composition readability and text legibility

Triggers self-correcting re-draws when off-model drift is detected.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from google.cloud import firestore  # type: ignore[import-untyped]

from backend import config
from backend.agents.bible_manager import BibleManager
from backend.agents.panel_generator import PanelGeneratorAgent
from backend.telemetry import trace_event
from backend.tools import cost_guard, gemini_vision, storage

log = logging.getLogger(__name__)

_db: firestore.Client | None = None


def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=config.PROJECT_ID or None)
    return _db


class ConsistencyCriticAgent:
    """Specialist vision critic agent running the self-correction verification loop."""

    def __init__(self, project_id: str, db_client: firestore.Client | None = None):
        self.project_id = project_id
        self._db = db_client or _get_db()
        self.bible_manager = BibleManager(project_id, self._db)
        self.panel_generator = PanelGeneratorAgent(project_id, self._db)

    def verify_and_correct_panel(
        self,
        panel: dict[str, Any],
        art_uri: str,
        style_phrase: str,
        style_ref_uri: Optional[str] = None,
        mode: str | None = None,
    ) -> str:
        """Run the vision critic loop. If drift is detected, re-draw with corrective feedback.

        Returns final art_uri.
        """
        panel_id = panel["id"]
        current_mode = mode or config.COST_MODE
        max_iters = config.max_critic_iters(current_mode)

        characters = self.bible_manager.list_characters()
        char_map = {c["name"]: c for c in characters}

        # Load reference sheets for characters
        sheets: dict[str, bytes] = {}
        for char_name in panel.get("charactersPresent", []):
            char = char_map.get(char_name, {})
            for s_uri in char.get("referenceSheetUris", [])[:1]:
                try:
                    sheets[char_name] = storage.download_bytes(s_uri)
                except Exception:
                    pass

        # Load reference sheets for locations
        locations = self.bible_manager.list_locations()
        loc_sheets: dict[str, bytes] = {}
        for loc in locations:
            loc_name = loc.get("name", "Location")
            for l_uri in loc.get("referenceSheetUris", [])[:1]:
                try:
                    loc_sheets[loc_name] = storage.download_bytes(l_uri)
                except Exception:
                    pass

        # Load style reference
        style_ref_bytes: Optional[bytes] = None
        if style_ref_uri:
            try:
                style_ref_bytes = storage.download_bytes(style_ref_uri)
            except Exception:
                pass

        current_art_uri = art_uri

        for critic_iter in range(max_iters):
            trace_event(
                self.project_id,
                "consistency_critic",
                "info",
                f"Critic pass {critic_iter + 1}/{max_iters} for panel {panel_id}...",
            )

            try:
                panel_bytes = storage.download_bytes(current_art_uri)
            except Exception as e:
                trace_event(self.project_id, "consistency_critic", "warn", f"Could not load panel bytes: {e}")
                break

            # 1. Character match critique
            char_verdict = {"results": []}
            if sheets:
                char_verdict = gemini_vision.critique_characters(panel_bytes, sheets)

            # 2. Location match critique
            loc_verdict = {"results": []}
            if loc_sheets:
                loc_verdict = gemini_vision.critique_locations(panel_bytes, loc_sheets)

            # 3. Style critique
            style_verdict = {"styleConsistent": True, "compositionReadable": True, "textOk": None}
            if style_ref_bytes:
                style_verdict = gemini_vision.critique_style_readability(panel_bytes, style_ref_bytes)

            all_chars = gemini_vision.all_characters_match(char_verdict) if sheets else True
            all_locs = gemini_vision.all_locations_match(loc_verdict) if loc_sheets else True
            style_ok = style_verdict.get("styleConsistent", True)
            readable = style_verdict.get("compositionReadable", True)

            char_status = "PASS" if all_chars else "FAIL"
            loc_status = "PASS" if all_locs else "FAIL"
            style_status = "PASS" if (style_ok and readable) else "FAIL"

            trace_event(
                self.project_id,
                "consistency_critic",
                "decision",
                f"[Three-Way Verdict] Panel {panel_id} (iter {critic_iter + 1}): Character={char_status} | Location={loc_status} | Style={style_status}",
            )

            if all_chars and all_locs and style_ok and readable:
                trace_event(
                    self.project_id,
                    "consistency_critic",
                    "decision",
                    f"✓ Panel {panel_id} passed three-way consistency & style critique (iteration {critic_iter + 1})",
                )
                self._db.collection("projects").document(self.project_id)\
                    .collection("panels").document(panel_id).update({
                        "status": "approved",
                        "criticIterations": critic_iter + 1,
                    })
                return current_art_uri

            # Drift detected
            notes = gemini_vision.build_corrective_notes(
                char_critique=char_verdict,
                style_critique=style_verdict,
                location_critique=loc_verdict,
            )
            drift_summary = []
            for r in char_verdict.get("results", []):
                if not r.get("match", True):
                    drift_summary.append(f"{r['name']}: {r.get('note', 'character drift')}")
            for r in loc_verdict.get("results", []):
                if not r.get("match", True):
                    drift_summary.append(f"Location {r['name']}: {r.get('note', 'environment drift')}")
            if not style_ok:
                drift_summary.append(f"Style: {style_verdict.get('notes', 'style drift')}")

            trace_event(
                self.project_id,
                "consistency_critic",
                "decision",
                f"✗ Panel {panel_id} drift detected: {'; '.join(drift_summary)}",
            )

            # Check if allowed to re-draw
            ok_redraw, _ = cost_guard.can_generate(self.project_id)
            if not ok_redraw or critic_iter >= max_iters - 1:
                trace_event(
                    self.project_id,
                    "consistency_critic",
                    "warn",
                    f"Panel {panel_id} flagged 'needs_review' (iterations exhausted / cap reached)",
                )
                self._db.collection("projects").document(self.project_id)\
                    .collection("panels").document(panel_id).update({
                        "status": "needs_review",
                        "criticIterations": critic_iter + 1,
                        "criticNotes": drift_summary,
                    })
                return current_art_uri

            # Re-draw with corrective feedback
            trace_event(
                self.project_id,
                "consistency_critic",
                "info",
                f"Autonomous re-draw: re-rendering panel {panel_id} with corrective guidance...",
            )

            new_uri, phash = self.panel_generator.draw_panel(
                panel=panel,
                style_phrase=style_phrase,
                style_ref_uri=style_ref_uri,
                corrective_notes=notes,
                mode=mode,
            )
            if new_uri:
                current_art_uri = new_uri

        return current_art_uri
