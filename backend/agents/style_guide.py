"""
Inkwell — Style Guide Agent (§8.2)

Establishes house art style reference and saves it to the Story Bible.
"""

from __future__ import annotations

import logging
from typing import Optional

from backend.agents.bible_manager import BibleManager
from backend.telemetry import trace_event
from backend.tools import gemini_image

log = logging.getLogger(__name__)


class StyleGuideAgent:
    """Specialist agent establishing and locking house art style."""

    def __init__(self, project_id: str, db_client: Any = None):
        self.project_id = project_id
        self._db = db_client
        self.bible_manager = BibleManager(project_id, db_client)

    def establish_style(
        self,
        style_phrase: str = "manga-influenced modern comic",
        palette: str = "vibrant",
        mode: str | None = None,
    ) -> Optional[str]:
        """Generate style guide sample panel and register in Story Bible."""
        existing = self.bible_manager.get_style_guide()
        if existing.get("styleReferenceUris"):
            return existing["styleReferenceUris"][0]

        trace_event(self.project_id, "style_guide", "info", f"Generating style reference: {style_phrase}...")

        try:
            style_uri = gemini_image.generate_style_reference(
                project_id=self.project_id,
                style_phrase=style_phrase,
                palette=palette,
                mode=mode,
            )
            self.bible_manager.set_style_guide(
                description=style_phrase,
                style_reference_uris=[style_uri],
                palette=palette,
                canonical_phrase=style_phrase,
            )
            trace_event(self.project_id, "style_guide", "decision", "✓ House art style locked in Story Bible")
            return style_uri
        except Exception as e:
            trace_event(self.project_id, "style_guide", "warn", f"Style reference error: {e}")
            return None
