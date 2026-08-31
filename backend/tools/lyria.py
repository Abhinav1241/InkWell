"""
Inkwell — Lyria Tool (Soundtrack / Score Generation)

Generates short background music tracks aligned with the comic's tone
using Google's Lyria audio foundation models on Vertex AI.
"""

from __future__ import annotations

import logging
from typing import Optional

from backend import config
from backend.tools import storage

log = logging.getLogger(__name__)


def generate_soundtrack(
    project_id: str,
    mood: str = "cinematic, dramatic, comic score",
    seconds: int = 15,
) -> Optional[str]:
    """Generate a short background audio track matching the comic's mood.

    Returns GCS URI to the .mp3/.wav file, or None if unavailable.
    """
    try:
        from google import genai
        client = genai.Client(
            vertexai=True,
            project=config.PROJECT_ID or None,
            location=config.VERTEX_LOCATION or config.REGION or "global",
        )

        prompt = f"Background instrumental score for a comic: {mood}. Duration: {seconds} seconds."
        log.info("Generating Lyria soundtrack for project %s (mood: %s)...", project_id, mood)

        # Generate audio using audio generation capabilities
        response = client.models.generate_audio(
            model="lyria",
            prompt=prompt,
        )

        audio_bytes = getattr(response, "audio_bytes", None)
        if not audio_bytes and hasattr(response, "candidates") and response.candidates:
            part = response.candidates[0].content.parts[0]
            if hasattr(part, "inline_data"):
                audio_bytes = part.inline_data.data

        if not audio_bytes:
            log.info("Lyria did not return raw audio bytes; skipping soundtrack upload")
            return None

        gcs_path = storage.gcs_path_for("motion", project_id, "soundtrack.mp3")
        uri = storage.upload_bytes(audio_bytes, gcs_path, content_type="audio/mp3")
        log.info("✓ Lyria soundtrack saved: %s", uri)
        return uri

    except Exception as e:
        log.info("Lyria generation skipped/unavailable: %s", e)
        return None
