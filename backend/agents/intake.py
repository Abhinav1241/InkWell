"""
Inkwell — Intake Agent (§8.2)

Gemini 3.5 Flash specialist for extracting story elements, conducting
clarifying Q&A interviews, and mutating the Story Bible.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from backend.agents.bible_manager import BibleManager
from backend.telemetry import trace_event
from backend.tools import gemini_text

log = logging.getLogger(__name__)


class IntakeAgent:
    """Specialist agent handling conversational story intake and direction."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.bible_manager = BibleManager(project_id)

    def process_story(self, raw_story: str) -> dict[str, Any]:
        """Extract premise, characters, tone and generate clarifying questions."""
        trace_event(self.project_id, "intake", "info", "Extracting story premise and cast...")
        extraction = gemini_text.extract_story(raw_story)

        # Seed core bible
        premise = extraction.get("logline", "")
        tone = extraction.get("tone", "cinematic")
        setting = extraction.get("setting", "")
        self.bible_manager.set_core_bible(premise, tone, setting)

        # Register extracted characters into memory bank
        for c in extraction.get("characters", []):
            char_id = uuid.uuid4().hex[:8]
            name = c.get("name", "Unknown")
            desc = c.get("description", "")
            self.bible_manager.upsert_character(
                char_id=char_id,
                name=name,
                role=c.get("role", "supporting"),
                description=desc,
                canonical_prompt_fragment=desc or f"{name}, character",
                reference_sheet_uris=[],
                approved=False,
            )

        trace_event(
            self.project_id,
            "intake",
            "decision",
            f"Intake complete: '{premise[:60]}' with {len(extraction.get('characters', []))} characters",
        )
        return extraction

    def handle_user_answers(self, answers: dict[str, str]) -> dict[str, Any]:
        """Mutate Story Bible based on user answers to clarifying questions."""
        trace_event(self.project_id, "intake", "info", "Mutating Story Bible from user direction...")
        current_bible = self.bible_manager.get_core_bible()
        updated = gemini_text.apply_answers(current_bible, answers)

        self.bible_manager.set_core_bible(
            premise=updated.get("premise", current_bible.get("premise", "")),
            tone=updated.get("tone", current_bible.get("tone", "")),
            setting=updated.get("setting", current_bible.get("setting", "")),
        )
        trace_event(self.project_id, "intake", "decision", "Story Bible updated from user feedback")
        return updated
