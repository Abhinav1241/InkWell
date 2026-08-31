"""
Inkwell — Cloud Storage Helpers

Upload/download to GCS with content-type awareness.
Signed URLs for frontend direct access.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Optional

from google.cloud import storage  # type: ignore[import-untyped]

from backend import config

log = logging.getLogger(__name__)

_client: storage.Client | None = None


def _get_client() -> storage.Client:
    global _client
    if _client is None:
        _client = storage.Client(project=config.PROJECT_ID or None)
    return _client


def _bucket() -> storage.Bucket:
    return _get_client().bucket(config.ASSETS_BUCKET)


# ── Content type mapping ────────────────────────────────────────────────────

_CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
    ".pdf": "application/pdf",
    ".json": "application/json",
}


def _content_type(path: str) -> str:
    for ext, ct in _CONTENT_TYPES.items():
        if path.lower().endswith(ext):
            return ct
    return "application/octet-stream"


# ── Upload / Download ───────────────────────────────────────────────────────

def upload_bytes(data: bytes, gcs_path: str, content_type: Optional[str] = None) -> str:
    """Upload bytes to GCS. Returns the gs:// URI."""
    blob = _bucket().blob(gcs_path)
    ct = content_type or _content_type(gcs_path)
    blob.upload_from_string(data, content_type=ct)
    uri = f"gs://{config.ASSETS_BUCKET}/{gcs_path}"
    log.info("Uploaded %d bytes → %s", len(data), uri)
    return uri


def download_bytes(gcs_path: str) -> bytes:
    """Download bytes from GCS."""
    # Strip gs:// prefix if present
    if gcs_path.startswith("gs://"):
        gcs_path = "/".join(gcs_path.split("/")[3:])
    blob = _bucket().blob(gcs_path)
    return blob.download_as_bytes()


def signed_download_url(gcs_path: str, expiration_minutes: int = 60) -> str:
    """Generate a signed download URL for frontend access."""
    if gcs_path.startswith("gs://"):
        gcs_path = "/".join(gcs_path.split("/")[3:])
    blob = _bucket().blob(gcs_path)
    return blob.generate_signed_url(
        expiration=timedelta(minutes=expiration_minutes),
        method="GET",
    )


def signed_upload_url(gcs_path: str, content_type: str = "image/png",
                      expiration_minutes: int = 30) -> str:
    """Generate a signed upload URL for direct client uploads."""
    blob = _bucket().blob(gcs_path)
    return blob.generate_signed_url(
        expiration=timedelta(minutes=expiration_minutes),
        method="PUT",
        content_type=content_type,
    )


def gcs_path_for(kind: str, project_id: str, *parts: str) -> str:
    """Build a standardized GCS path.

    Examples:
        gcs_path_for("characters", pid, char_id, "sheet-0.png")
        gcs_path_for("panels", pid, panel_id, "art.png")
        gcs_path_for("pages", pid, "page-0.png")
        gcs_path_for("exports", pid, "comic.pdf")
    """
    return "/".join([kind, project_id, *parts])
