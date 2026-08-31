"""
Inkwell — Letterer Agent (§8.2)

Composites dialogue speech bubbles, thought bubbles, and caption boxes over panel art.
Zero model cost. Re-lettering NEVER triggers image regeneration.
"""

from __future__ import annotations

import logging
from typing import Any

from google.cloud import firestore  # type: ignore[import-untyped]

from backend import config
from backend.telemetry import trace_event
from backend.tools import compositor, storage

log = logging.getLogger(__name__)

_db: firestore.Client | None = None


def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=config.PROJECT_ID or None)
    return _db


class LettererAgent:
    """Specialist agent for overlaying typography and speech bubbles."""

    def __init__(self, project_id: str, db_client: firestore.Client | None = None):
        self.project_id = project_id
        self._db = db_client or _get_db()

    def letter_panels(self, panels: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Letter all approved/generated panels in a comic."""
        trace_event(self.project_id, "lettering", "info", f"Lettering {len(panels)} panels...")
        lettered_list = []

        for p in panels:
            panel_id = p["id"]
            art_uri = p.get("artUri")

            if not art_uri or p.get("status") in ("failed", "skipped_capped"):
                lettered_list.append(p)
                continue

            try:
                art_bytes = storage.download_bytes(art_uri)
                dialogue = p.get("dialogue", [])
                caption = p.get("caption", "")

                lettered_bytes = compositor.letter_panel(
                    art_bytes=art_bytes,
                    dialogue=dialogue,
                    caption=caption,
                )

                gcs_path = storage.gcs_path_for("panels", self.project_id, panel_id, "lettered.png")
                lettered_uri = storage.upload_bytes(lettered_bytes, gcs_path)

                self._db.collection("projects").document(self.project_id)\
                    .collection("panels").document(panel_id).update({
                        "letteredUri": lettered_uri,
                    })

                p["letteredUri"] = lettered_uri
                p["letteredBytes"] = lettered_bytes
                lettered_list.append(p)

                trace_event(self.project_id, "lettering", "info", f"✓ Lettered panel {panel_id}")

            except Exception as e:
                trace_event(self.project_id, "lettering", "warn", f"Lettering failed for {panel_id}: {e}")
                lettered_list.append(p)

        return lettered_list
