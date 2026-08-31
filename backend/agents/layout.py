"""
Inkwell — Layout Agent (§8.2)

Arranges lettered panels into page layouts with clean gutters, borders, and reading order.
Zero model cost.
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


class LayoutAgent:
    """Specialist agent composing lettered panels into full page images."""

    def __init__(self, project_id: str, db_client: firestore.Client | None = None):
        self.project_id = project_id
        self._db = db_client or _get_db()

    def layout_pages(self, panels: list[dict[str, Any]]) -> list[bytes]:
        """Group panels by pageIndex and compose full page images.

        Returns list of page PNG bytes.
        """
        trace_event(self.project_id, "layout", "info", "Composing page layouts and gutters...")

        # Group by pageIndex
        by_page: dict[int, list[dict[str, Any]]] = {}
        for p in panels:
            pi = p.get("pageIndex", 0)
            by_page.setdefault(pi, []).append(p)

        page_images: list[bytes] = []

        for page_idx in sorted(by_page.keys()):
            page_panels = sorted(by_page[page_idx], key=lambda x: x.get("order", 0))

            panel_bytes_list = []
            for p in page_panels:
                if "letteredBytes" in p:
                    panel_bytes_list.append(p["letteredBytes"])
                elif p.get("letteredUri"):
                    try:
                        panel_bytes_list.append(storage.download_bytes(p["letteredUri"]))
                    except Exception:
                        pass
                elif p.get("artUri"):
                    try:
                        panel_bytes_list.append(storage.download_bytes(p["artUri"]))
                    except Exception:
                        pass

            if not panel_bytes_list:
                continue

            page_bytes = compositor.compose_page(panel_bytes_list)
            gcs_path = storage.gcs_path_for("pages", self.project_id, f"page-{page_idx}.png")
            page_uri = storage.upload_bytes(page_bytes, gcs_path)
            page_images.append(page_bytes)

            # Update page doc in Firestore
            for doc in self._db.collection("projects").document(self.project_id)\
                    .collection("pages").where("index", "==", page_idx).stream():
                self._db.collection("projects").document(self.project_id)\
                    .collection("pages").document(doc.id).update({
                        "pageImageUri": page_uri,
                        "status": "done",
                    })

            trace_event(
                self.project_id,
                "layout",
                "info",
                f"✓ Page {page_idx + 1} assembled ({len(panel_bytes_list)} panels)",
            )

        return page_images
