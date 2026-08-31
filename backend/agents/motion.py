"""
Inkwell — Motion Comic & Audio Agent (Bonus Models)

Orchestrates Veo 3.1 video animation, Lyria soundtrack scoring, and Cloud TTS narration.
⚠️ Guarded by cost_guard.veo_enabled(mode) — runs ONLY in FINAL mode.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from google.cloud import firestore  # type: ignore[import-untyped]

from backend import config
from backend.agents.bible_manager import BibleManager
from backend.telemetry import trace_event
from backend.tools import cost_guard, lyria, storage, tts, veo

log = logging.getLogger(__name__)

_db: firestore.Client | None = None


def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=config.PROJECT_ID or None)
    return _db


class MotionAgent:
    """Specialist agent generating multimedia teaser deliverables."""

    def __init__(self, project_id: str, db_client: firestore.Client | None = None):
        self.project_id = project_id
        self._db = db_client or _get_db()
        self.bible_manager = BibleManager(project_id, self._db)

    def generate_teaser(
        self,
        hero_panel: dict[str, Any],
        mode: str | None = None,
    ) -> dict[str, Optional[str]]:
        """Generate a motion-comic video teaser, music score, and narration.

        Returns: {"motionUri": str|None, "soundtrackUri": str|None, "narrationUri": str|None}
        """
        current_mode = mode or config.COST_MODE
        result: dict[str, Optional[str]] = {
            "motionUri": None,
            "soundtrackUri": None,
            "narrationUri": None,
        }

        if not cost_guard.veo_enabled(current_mode):
            trace_event(self.project_id, "motion", "info", f"Motion teaser skipped: '{current_mode}' is not FINAL mode")
            return result

        trace_event(self.project_id, "motion", "info", "Producing motion-comic teaser with Veo 3.1 & Lyria...")

        art_uri = hero_panel.get("artUri")
        if not art_uri:
            return result

        try:
            panel_bytes = storage.download_bytes(art_uri)
            action = hero_panel.get("action", "Cinematic action shot")

            # Reference sheet for consistency
            ref_bytes = None
            for char_name in hero_panel.get("charactersPresent", []):
                refs = self.bible_manager.get_character_references_by_names([char_name])
                if refs:
                    try:
                        ref_bytes = storage.download_bytes(refs[0])
                        break
                    except Exception:
                        pass

            # 1. Veo Video
            motion_uri = veo.animate_hero_panel(
                project_id=self.project_id,
                hero_panel_png_bytes=panel_bytes,
                prompt=f"Cinematic motion comic animation: {action}",
                reference_png_bytes=ref_bytes,
                seconds=4,
                mode=current_mode,
            )
            result["motionUri"] = motion_uri

            # 2. Lyria Soundtrack
            bible = self.bible_manager.get_core_bible()
            tone = bible.get("tone", "dramatic")
            soundtrack_uri = lyria.generate_soundtrack(
                project_id=self.project_id,
                mood=f"{tone} comic teaser soundtrack",
                seconds=10,
            )
            result["soundtrackUri"] = soundtrack_uri

            # 3. TTS Narration for hero caption/dialogue
            caption = hero_panel.get("caption", "")
            if caption:
                narration_uri = tts.narrate_text(
                    text=caption,
                    project_id=self.project_id,
                    output_filename="teaser_narration.mp3",
                )
                result["narrationUri"] = narration_uri

            trace_event(self.project_id, "motion", "decision", "✓ Motion-comic teaser package compiled")

        except Exception as e:
            trace_event(self.project_id, "motion", "warn", f"Motion generation error: {e}")

        return result
