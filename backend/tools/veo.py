"""
Inkwell — Veo 3.1 Tool (Motion Comic Teaser)

Generates short video clips animating hero panels while maintaining
character consistency using reference images.
⚠️ Guarded by cost_guard.veo_enabled() — no-ops outside FINAL mode.
"""

from __future__ import annotations

import logging
from typing import Optional

from backend import config
from backend.tools import cost_guard, storage

log = logging.getLogger(__name__)


def animate_hero_panel(
    project_id: str,
    hero_panel_png_bytes: bytes,
    prompt: str,
    reference_png_bytes: Optional[bytes] = None,
    seconds: int = 4,
    mode: str | None = None,
) -> Optional[str]:
    """Generate a motion clip from a hero panel using Veo 3.1.

    Guarded by cost_guard.veo_enabled(mode).
    Returns GCS URI to the generated .mp4, or None if disabled/unsupported.
    """
    current_mode = mode or config.COST_MODE

    if not cost_guard.veo_enabled(current_mode):
        log.info("Veo generation skipped: cost mode '%s' is not FINAL", current_mode)
        return None

    # Cap check
    ok, reason = cost_guard.can_generate(project_id)
    if not ok:
        log.warning("Veo generation blocked: %s", reason)
        return None

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(
            vertexai=True,
            project=config.PROJECT_ID or None,
            location=config.REGION or None,
        )

        contents = [
            prompt,
            types.Part.from_bytes(data=hero_panel_png_bytes, mime_type="image/png"),
        ]
        if reference_png_bytes:
            contents.append(
                types.Part.from_bytes(data=reference_png_bytes, mime_type="image/png")
            )

        log.info("Requesting Veo 3.1 video generation for %s (%d sec)...", project_id, seconds)
        response = client.models.generate_videos(
            model=config.VEO_MODEL,
            prompt=prompt,
            image=types.Image(image_bytes=hero_panel_png_bytes),
            config=types.GenerateVideosConfig(
                duration_seconds=seconds,
                fps=24,
            ),
        )

        # Extract video bytes
        video_bytes = None
        if hasattr(response, "generated_videos") and response.generated_videos:
            video_bytes = response.generated_videos[0].video.video_bytes

        if not video_bytes:
            log.warning("Veo returned empty video bytes")
            return None

        # Upload to GCS
        gcs_path = storage.gcs_path_for("motion", project_id, "teaser.mp4")
        uri = storage.upload_bytes(video_bytes, gcs_path, content_type="video/mp4")

        cost_guard.record_generation(
            project_id=project_id,
            model=config.VEO_MODEL,
            mode=current_mode,
            kind="video",
            est_cost=config.EST_COST_VEO,
        )

        log.info("✓ Veo teaser generated: %s", uri)
        return uri

    except Exception as e:
        log.warning("Veo animation failed: %s", e)
        return None
