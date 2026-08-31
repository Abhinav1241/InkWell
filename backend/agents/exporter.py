"""
Inkwell — Exporter Agent (§8.2)

Builds final web reader manifest, downloadable PDF, and exports Story Bible JSON sidecar.
Zero model cost.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from google.cloud import firestore  # type: ignore[import-untyped]

from backend import config
from backend.telemetry import trace_event
from backend.tools import cost_guard, pdf, storage

log = logging.getLogger(__name__)

_db: firestore.Client | None = None


def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=config.PROJECT_ID or None)
    return _db


class ExporterAgent:
    """Specialist agent producing downloadable and web-ready deliverables."""

    def __init__(self, project_id: str, db_client: firestore.Client | None = None):
        self.project_id = project_id
        self._db = db_client or _get_db()

    def export_comic(self, page_images: list[bytes], title: str = "Inkwell Comic") -> dict[str, Any]:
        """Generate PDF, reader manifest JSON, and bible sidecar."""
        trace_event(self.project_id, "export", "info", "Compiling PDF and web reader manifest...")
        result: dict[str, Any] = {}

        # 1. PDF export
        if page_images:
            pdf_bytes = pdf.build_pdf(page_images, title=title)
            pdf_path = storage.gcs_path_for("exports", self.project_id, "comic.pdf")
            pdf_uri = storage.upload_bytes(pdf_bytes, pdf_path)
            result["pdfUri"] = pdf_uri
            trace_event(self.project_id, "export", "decision", f"✓ PDF generated ({len(page_images)} pages)")

        # 2. Reader Manifest JSON
        reader_manifest = {
            "projectId": self.project_id,
            "title": title,
            "pages": [],
        }

        for doc in self._db.collection("projects").document(self.project_id)\
                .collection("pages").order_by("index").stream():
            p_data = doc.to_dict() or {}
            if p_data.get("pageImageUri"):
                reader_manifest["pages"].append({
                    "index": p_data.get("index", 0),
                    "imageUri": p_data["pageImageUri"],
                })

        manifest_path = storage.gcs_path_for("exports", self.project_id, "reader.json")
        manifest_uri = storage.upload_bytes(
            json.dumps(reader_manifest, indent=2).encode(),
            manifest_path,
        )
        result["readerManifestUri"] = manifest_uri

        # 3. Story Bible JSON sidecar
        bible_sidecar = {
            "projectId": self.project_id,
            "title": title,
            "characters": [],
            "style": {},
            "panels": [],
        }
        for doc in self._db.collection("projects").document(self.project_id)\
                .collection("characters").stream():
            bible_sidecar["characters"].append(doc.to_dict())

        style_doc = self._db.collection("projects").document(self.project_id)\
            .collection("bible").document("style").get()
        if style_doc.exists:
            bible_sidecar["style"] = style_doc.to_dict()

        for doc in self._db.collection("projects").document(self.project_id)\
                .collection("panels").order_by("order").stream():
            bible_sidecar["panels"].append(doc.to_dict())

        sidecar_path = storage.gcs_path_for("exports", self.project_id, "story_bible.json")
        sidecar_uri = storage.upload_bytes(
            json.dumps(bible_sidecar, indent=2).encode(),
            sidecar_path,
        )
        result["bibleJsonUri"] = sidecar_uri

        # Run cost summary
        summary = cost_guard.run_cost_summary(self.project_id)
        trace_event(self.project_id, "export", "info", f"Final run spend ledger: {summary}")

        return result
