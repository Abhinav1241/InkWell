"""
Inkwell — Character Designer Agent (§8.2)

Designs character reference sheets (turnaround angles + expressions)
and registers canonical prompt fragments in the Story Bible.
"""

from __future__ import annotations

import logging
from typing import Any

from backend import config
from backend.agents.bible_manager import BibleManager
from backend.telemetry import trace_event
from backend.tools import gemini_image

log = logging.getLogger(__name__)


class CharacterDesignerAgent:
    """Specialist agent for character consistency sheet design."""

    def __init__(self, project_id: str, db_client: Any = None):
        self.project_id = project_id
        self._db = db_client
        self.bible_manager = BibleManager(project_id, db_client)

    def design_cast(
        self,
        style_phrase: str,
        mode: str | None = None,
        max_characters: int | None = None,
    ) -> list[dict[str, Any]]:
        """Generate consistency turnaround sheets for up to max_characters."""
        max_chars = max_characters if max_characters is not None else config.MAX_MAIN_CHARACTERS
        characters = self.bible_manager.list_characters()
        # Prioritize protagonist or primary named characters
        characters.sort(key=lambda c: (
            0 if c.get("role") == "protagonist" else 1,
            0 if c.get("name", "").lower() in ("elara", "vance") else 1,
        ))
        designed = []

        for char in characters[:max_chars]:
            char_id = char["id"]
            name = char["name"]
            desc = char.get("description", "")
            canonical = char.get("canonicalPromptFragment") or desc or name

            if char.get("referenceSheetUris"):
                trace_event(self.project_id, "character_design", "info", f"Sheet already exists for {name}")
                designed.append(char)
                continue

            trace_event(self.project_id, "character_design", "info", f"Generating reference sheet for {name}...")

            try:
                sheet_uris = gemini_image.generate_character_sheet(
                    project_id=self.project_id,
                    char_id=char_id,
                    name=name,
                    description=desc,
                    style=style_phrase,
                    mode=mode,
                )

                self.bible_manager.upsert_character(
                    char_id=char_id,
                    name=name,
                    role=char.get("role", "supporting"),
                    description=desc,
                    canonical_prompt_fragment=canonical,
                    reference_sheet_uris=sheet_uris,
                    approved=True,
                )
                char["referenceSheetUris"] = sheet_uris
                char["canonicalPromptFragment"] = canonical
                designed.append(char)

                trace_event(
                    self.project_id,
                    "character_design",
                    "decision",
                    f"✓ Reference sheet locked for {name} ({len(sheet_uris)} images)",
                )

            except Exception as e:
                trace_event(self.project_id, "character_design", "warn", f"Sheet generation error for {name}: {e}")
                designed.append(char)

        return designed
