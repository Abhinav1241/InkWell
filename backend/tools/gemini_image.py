"""
Inkwell — Gemini Image Tool

All image generation routes through CostGuard.
Supports character sheets and panel art with reference images.
The expensive model ID is NEVER hardcoded — always resolved via cost_guard.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from google import genai
from google.genai import types

from backend import config
from backend.tools import cost_guard, storage

log = logging.getLogger(__name__)

_client: genai.Client | None = None
_last_image_call_ts: float = 0.0
IMAGE_CALL_INTERVAL_SEC: float = 15.0


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=config.PROJECT_ID,
            location=config.REGION,
        )
    return _client


def _throttle_image_calls(interval: float = IMAGE_CALL_INTERVAL_SEC) -> None:
    """Enforce a minimum delay between image generation API calls to prevent 429s."""
    global _last_image_call_ts
    now = time.time()
    elapsed = now - _last_image_call_ts
    if _last_image_call_ts > 0 and elapsed < interval:
        wait_time = interval - elapsed
        log.info("Rate limit throttle: waiting %.1fs before next image generation...", wait_time)
        time.sleep(wait_time)
    _last_image_call_ts = time.time()


def _generate_image_with_retry(
    client: genai.Client,
    model: str,
    contents: list[Any],
    config_obj: types.GenerateContentConfig,
    max_retries: int = 5,
    initial_backoff: float = 15.0,
) -> Any:
    """Call generate_content with throttling and exponential backoff on 429."""
    for attempt in range(max_retries + 1):
        _throttle_image_calls()
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config_obj,
            )
        except Exception as e:
            err_str = str(e)
            is_429 = (
                "429" in err_str
                or "RESOURCE_EXHAUSTED" in err_str
                or "ResourceExhausted" in err_str
                or "Too Many Requests" in err_str
            )
            if is_429 and attempt < max_retries:
                backoff = initial_backoff * (2 ** attempt)
                log.warning(
                    "Image generation rate-limited (429/RESOURCE_EXHAUSTED). Retrying in %.1fs (attempt %d/%d)...",
                    backoff,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(backoff)
            else:
                raise


def generate_character_sheet(
    project_id: str,
    char_id: str,
    name: str,
    description: str,
    style: str,
    key_emotion: str = "determined",
    mode: str | None = None,
) -> list[str]:
    """P2: Generate a character reference/consistency sheet.

    In FINAL mode, uses the Pro image model (per spec amendment).
    Returns a list of GCS URIs for the sheet image(s).

    Raises ValueError if image cap is reached.
    """
    from backend.prompts.prompts import P2_CHARACTER_SHEET

    current_mode = mode or config.COST_MODE

    # Cap check
    ok, reason = cost_guard.can_generate(project_id)
    if not ok:
        raise ValueError(f"Cannot generate character sheet: {reason}")

    # Build prompt
    prompt = P2_CHARACTER_SHEET.format(
        style_phrase=style,
        name=name,
        canonical_prompt_fragment=description,
        key_emotion=key_emotion,
    )

    # Use Pro model for sheets in FINAL mode (per spec amendment)
    model = config.sheet_image_model(current_mode)

    # Check cache
    ref_uris: list[str] = []
    phash = cost_guard.prompt_hash(prompt, ref_uris, model)
    cached = cost_guard.cached_image(project_id, phash)
    if cached:
        return [cached]

    # Generate
    client = _get_client()
    params = cost_guard.image_params_for_mode(current_mode)

    response = _generate_image_with_retry(
        client=client,
        model=model,
        contents=[prompt],
        config_obj=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=params.get("aspect_ratio", "1:1"),
            ),
        ),
    )

    # Extract image bytes
    uris: list[str] = []
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            image_bytes = part.inline_data.data
            gcs_path = storage.gcs_path_for(
                "characters", project_id, char_id,
                f"sheet-{len(uris)}.png",
            )
            uri = storage.upload_bytes(image_bytes, gcs_path)
            uris.append(uri)

    if not uris:
        raise RuntimeError("Image model returned no image data for character sheet")

    # Record cost
    cost_guard.record_generation(
        project_id, model, current_mode, "image",
    )

    log.info("Generated character sheet for %s: %d images", name, len(uris))
    return uris


def generate_location_sheet(
    project_id: str,
    loc_id: str,
    name: str,
    description: str,
    style: str,
    mode: str | None = None,
) -> list[str]:
    """P2b: Generate a location/environment consistency reference sheet.

    In FINAL mode, uses the Pro image model (per spec amendment).
    Returns a list of GCS URIs for the location sheet image(s).

    Raises ValueError if image cap is reached.
    """
    from backend.prompts.prompts import P2B_LOCATION_SHEET

    current_mode = mode or config.COST_MODE

    # Cap check
    ok, reason = cost_guard.can_generate(project_id)
    if not ok:
        raise ValueError(f"Cannot generate location sheet: {reason}")

    # Build prompt
    prompt = P2B_LOCATION_SHEET.format(
        style_phrase=style,
        name=name,
        canonical_prompt_fragment=description,
    )

    # Use Pro model for sheets in FINAL mode
    model = config.sheet_image_model(current_mode)

    # Check cache
    ref_uris: list[str] = []
    phash = cost_guard.prompt_hash(prompt, ref_uris, model)
    cached = cost_guard.cached_image(project_id, phash)
    if cached:
        return [cached]

    # Generate
    client = _get_client()
    params = cost_guard.image_params_for_mode(current_mode)

    response = _generate_image_with_retry(
        client=client,
        model=model,
        contents=[prompt],
        config_obj=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=params.get("aspect_ratio", "3:4"),
            ),
        ),
    )

    # Extract image bytes
    uris: list[str] = []
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            image_bytes = part.inline_data.data
            gcs_path = storage.gcs_path_for(
                "locations", project_id, loc_id,
                f"sheet-{len(uris)}.png",
            )
            uri = storage.upload_bytes(image_bytes, gcs_path)
            uris.append(uri)

    if not uris:
        raise RuntimeError("Image model returned no image data for location sheet")

    # Record cost
    cost_guard.record_generation(
        project_id, model, current_mode, "image",
    )

    log.info("Generated location sheet for %s: %d images", name, len(uris))
    return uris


def generate_panel(
    project_id: str,
    panel_id: str,
    prompt: str,
    reference_image_uris: list[str],
    page_index: int = 0,
    seed: Optional[int] = None,
    aspect: Optional[str] = None,
    mode: str | None = None,
) -> tuple[str, str]:
    """P4: Generate a single comic panel.

    Passes character reference sheets as reference inputs for consistency.
    Routes through CostGuard for cap check, cache, and ledger.

    Returns the GCS URI of the generated panel art.
    Raises ValueError if image cap is reached.
    """
    current_mode = mode or config.COST_MODE

    # Cap check
    ok, reason = cost_guard.can_generate(project_id)
    if not ok:
        raise ValueError(f"Cannot generate panel: {reason}")

    # Resolve model (NEVER hardcoded)
    model = cost_guard.image_model_for_mode(current_mode)

    # Check cache
    phash = cost_guard.prompt_hash(prompt, reference_image_uris, model, seed)
    cached = cost_guard.cached_image(project_id, phash)
    if cached:
        return cached

    # Build contents: prompt + reference images
    contents: list = [prompt]

    for ref_uri in reference_image_uris:
        try:
            ref_bytes = storage.download_bytes(ref_uri)
            contents.append(
                types.Part.from_bytes(data=ref_bytes, mime_type="image/png")
            )
        except Exception as e:
            log.warning("Failed to load reference image %s: %s", ref_uri, e)

    # Generate
    client = _get_client()
    params = cost_guard.image_params_for_mode(current_mode)
    img_aspect = aspect or params.get("aspect_ratio", "3:4")

    response = _generate_image_with_retry(
        client=client,
        model=model,
        contents=contents,
        config_obj=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=img_aspect,
            ),
        ),
    )

    # Extract image
    image_bytes: bytes | None = None
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            image_bytes = part.inline_data.data
            break

    if not image_bytes:
        raise RuntimeError(f"Image model returned no image data for panel {panel_id}")

    # Upload
    gcs_path = storage.gcs_path_for("panels", project_id, panel_id, "art.png")
    uri = storage.upload_bytes(image_bytes, gcs_path)

    # Record cost
    cost_guard.record_generation(
        project_id, model, current_mode, "image", panel_id,
    )

    log.info("Generated panel %s (model=%s, mode=%s)", panel_id, model, current_mode)
    return uri, phash  # Return both URI and hash for panel doc


def generate_style_reference(
    project_id: str,
    style_phrase: str,
    palette: str = "vibrant",
    mode: str | None = None,
) -> str:
    """Generate a style guide reference image.

    Returns GCS URI.
    """
    from backend.prompts.prompts import P_STYLE_GUIDE

    current_mode = mode or config.COST_MODE

    ok, reason = cost_guard.can_generate(project_id)
    if not ok:
        raise ValueError(f"Cannot generate style reference: {reason}")

    prompt = P_STYLE_GUIDE.format(style_phrase=style_phrase, palette=palette)
    model = cost_guard.image_model_for_mode(current_mode)

    phash = cost_guard.prompt_hash(prompt, [], model)
    cached = cost_guard.cached_image(project_id, phash)
    if cached:
        return cached

    client = _get_client()
    params = cost_guard.image_params_for_mode(current_mode)

    response = _generate_image_with_retry(
        client=client,
        model=model,
        contents=[prompt],
        config_obj=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=params.get("aspect_ratio", "3:4"),
            ),
        ),
    )

    image_bytes: bytes | None = None
    for part in response.candidates[0].content.parts:
        if hasattr(part, "inline_data") and part.inline_data:
            image_bytes = part.inline_data.data
            break

    if not image_bytes:
        raise RuntimeError("Image model returned no image data for style reference")

    gcs_path = storage.gcs_path_for("style", project_id, "style-ref.png")
    uri = storage.upload_bytes(image_bytes, gcs_path)

    cost_guard.record_generation(project_id, model, current_mode, "image")
    log.info("Generated style reference for project %s", project_id)
    return uri
