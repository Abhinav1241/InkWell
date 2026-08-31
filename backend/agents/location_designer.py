"""
Inkwell — Location Designer Agent (§8.2)

Designs location and environment consistency reference sheets
and registers canonical prompt fragments in the Story Bible.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from backend import config
from backend.agents.bible_manager import BibleManager
from backend.telemetry import trace_event
from backend.tools import gemini_image

log = logging.getLogger(__name__)


class LocationDesignerAgent:
    """Specialist agent for location and environment consistency reference sheets."""

    def __init__(self, project_id: str, db_client: Any = None):
        self.project_id = project_id
        self._db = db_client
        self.bible_manager = BibleManager(project_id, db_client)

    def design_locations(self, style_phrase: str, mode: str | None = None) -> list[dict[str, Any]]:
        """Generate consistency reference sheets for key story locations."""
        locations = self.bible_manager.list_locations()

        # If no explicit locations registered, synthesize primary setting from core bible
        if not locations:
            bible = self.bible_manager.get_core_bible()
            setting = bible.get("setting", "")
            premise = bible.get("premise", "")
            if setting or premise:
                loc_id = f"loc_{uuid.uuid4().hex[:8]}"
                loc_name = setting.split(",")[0].strip() if setting else "Main Setting"
                if len(loc_name) > 40:
                    loc_name = "Primary Setting"
                loc_desc = setting or premise
                self.bible_manager.upsert_location(
                    loc_id=loc_id,
                    name=loc_name,
                    description=loc_desc,
                    canonical_prompt_fragment=loc_desc,
                    reference_sheet_uris=[],
                    approved=True,
                )
                locations = self.bible_manager.list_locations()

        designed = []
        for loc in locations[:2]:  # Limit to key locations per project
            loc_id = loc["id"]
            name = loc["name"]
            desc = loc.get("description", "")
            canonical = loc.get("canonicalPromptFragment") or desc or name

            if loc.get("referenceSheetUris"):
                trace_event(self.project_id, "location_design", "info", f"Sheet already exists for {name}")
                designed.append(loc)
                continue

            trace_event(self.project_id, "location_design", "info", f"Generating location reference sheet for {name}...")

            try:
                sheet_uris = gemini_image.generate_location_sheet(
                    project_id=self.project_id,
                    loc_id=loc_id,
                    name=name,
                    description=desc,
                    style=style_phrase,
                    mode=mode,
                )

                self.bible_manager.upsert_location(
                    loc_id=loc_id,
                    name=name,
                    description=desc,
                    canonical_prompt_fragment=canonical,
                    reference_sheet_uris=sheet_uris,
                    approved=True,
                )
                loc["referenceSheetUris"] = sheet_uris
                loc["canonicalPromptFragment"] = canonical
                designed.append(loc)

                trace_event(
                    self.project_id,
                    "location_design",
                    "decision",
                    f"✓ Location reference sheet locked for {name} ({len(sheet_uris)} images)",
                )

            except Exception as e:
                trace_event(self.project_id, "location_design", "warn", f"Location sheet generation error for {name}: {e}")
                designed.append(loc)

        return designed
