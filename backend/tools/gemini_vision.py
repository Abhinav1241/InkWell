"""
Inkwell — Gemini Vision Critic Tool

Uses gemini-3.5-flash vision to evaluate panel consistency against
character reference sheets and style guide. This is CHEAP (text model
with image inputs) — the RE-DRAWS are what cost money.
"""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from google import genai
from google.genai import types

from backend import config

log = logging.getLogger(__name__)

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=config.PROJECT_ID or None,
            location=config.VERTEX_LOCATION,
        )
    return _client


def _parse_json(text: str) -> Any:
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    return json.loads(cleaned)


def _generate_with_retry(
    client: genai.Client,
    model: str,
    contents: list[Any],
    config_obj: types.GenerateContentConfig,
    max_retries: int = 5,
    initial_backoff: float = 4.0,
) -> Any:
    """Execute generate_content with exponential backoff on 429/RESOURCE_EXHAUSTED."""
    for attempt in range(max_retries + 1):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config_obj,
            )
        except Exception as e:
            err_str = str(e)
            is_rate_limit = (
                "429" in err_str
                or "RESOURCE_EXHAUSTED" in err_str
                or "ResourceExhausted" in err_str
                or "Too Many Requests" in err_str
            )
            if is_rate_limit and attempt < max_retries:
                backoff = initial_backoff * (2 ** attempt)
                log.warning(
                    "Gemini Vision rate-limited (429/RESOURCE_EXHAUSTED). Retrying in %.1fs (attempt %d/%d)...",
                    backoff,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(backoff)
            else:
                raise


def critique_characters(
    panel_png: bytes,
    character_sheets: dict[str, bytes],
) -> dict[str, Any]:
    """P5: Vision critique — does each character match their reference sheet?

    Args:
        panel_png: The generated panel image bytes.
        character_sheets: {character_name: reference_sheet_bytes}

    Returns:
        {"results": [{"name": str, "match": bool, "note": str}]}
    """
    from backend.prompts.prompts import P5_CHARACTER_CRITIC

    character_names = list(character_sheets.keys())
    prompt_text = P5_CHARACTER_CRITIC.format(
        character_names=", ".join(character_names),
    )

    # Build multimodal contents: panel image + reference sheets + prompt
    contents: list = [
        "Panel image to evaluate:",
        types.Part.from_bytes(data=panel_png, mime_type="image/png"),
    ]

    for name, sheet_bytes in character_sheets.items():
        contents.append(f"Reference sheet for {name}:")
        contents.append(
            types.Part.from_bytes(data=sheet_bytes, mime_type="image/png")
        )

    contents.append(prompt_text)

    client = _get_client()
    response = _generate_with_retry(
        client=client,
        model=config.TEXT_MODEL,
        contents=contents,
        config_obj=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,  # Low temp for consistent judgments
        ),
    )

    result = _parse_json(response.text or "{}")
    log.info("Character critique: %s", result)
    return result


def critique_locations(
    panel_png: bytes,
    location_sheets: dict[str, bytes],
) -> dict[str, Any]:
    """P5c: Vision critique — does the environment match the location reference sheet?

    Args:
        panel_png: The generated panel image bytes.
        location_sheets: {location_name: reference_sheet_bytes}

    Returns:
        {"results": [{"name": str, "match": bool, "note": str}]}
    """
    from backend.prompts.prompts import P5C_LOCATION_CRITIC

    location_names = list(location_sheets.keys())
    prompt_text = P5C_LOCATION_CRITIC.format(
        location_names=", ".join(location_names),
    )

    contents: list = [
        "Panel image to evaluate:",
        types.Part.from_bytes(data=panel_png, mime_type="image/png"),
    ]

    for name, sheet_bytes in location_sheets.items():
        contents.append(f"Reference sheet for location {name}:")
        contents.append(
            types.Part.from_bytes(data=sheet_bytes, mime_type="image/png")
        )

    contents.append(prompt_text)

    client = _get_client()
    response = _generate_with_retry(
        client=client,
        model=config.TEXT_MODEL,
        contents=contents,
        config_obj=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )

    result = _parse_json(response.text or "{}")
    log.info("Location critique: %s", result)
    return result


def critique_style_readability(
    panel_png: bytes,
    style_ref_png: bytes,
    expected_text: str | None = None,
) -> dict[str, Any]:
    """P5b: Vision critique — style consistency + readability.

    Returns:
        {"styleConsistent": bool, "compositionReadable": bool,
         "textOk": bool|null, "notes": str}
    """
    from backend.prompts.prompts import P5B_STYLE_CRITIC

    contents: list = [
        "Comic panel to evaluate:",
        types.Part.from_bytes(data=panel_png, mime_type="image/png"),
        "Style reference:",
        types.Part.from_bytes(data=style_ref_png, mime_type="image/png"),
        P5B_STYLE_CRITIC,
    ]

    client = _get_client()
    response = _generate_with_retry(
        client=client,
        model=config.TEXT_MODEL,
        contents=contents,
        config_obj=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2,
        ),
    )

    result = _parse_json(response.text or "{}")
    log.info("Style/readability critique: %s", result)
    return result


def all_characters_match(critique_result: dict[str, Any]) -> bool:
    """Check if all characters passed the consistency check."""
    results = critique_result.get("results", [])
    return all(r.get("match", False) for r in results)


def all_locations_match(critique_result: dict[str, Any]) -> bool:
    """Check if all locations passed the consistency check."""
    results = critique_result.get("results", [])
    return all(r.get("match", False) for r in results)


def build_corrective_notes(
    char_critique: dict[str, Any] | None = None,
    style_critique: dict[str, Any] | None = None,
    location_critique: dict[str, Any] | None = None,
) -> str:
    """Build a corrective prompt fragment from three-way critic verdicts.

    This is appended to the original panel prompt for re-drawing.
    """
    notes: list[str] = []

    # Character corrections
    if char_critique:
        for r in char_critique.get("results", []):
            if not r.get("match", True):
                notes.append(
                    f"FIX {r['name']}: {r.get('note', 'does not match character reference')}"
                )

    # Location corrections
    if location_critique:
        for r in location_critique.get("results", []):
            if not r.get("match", True):
                notes.append(
                    f"FIX LOCATION ({r['name']}): {r.get('note', 'does not match location reference')}"
                )

    # Style corrections
    if style_critique:
        if not style_critique.get("styleConsistent", True):
            notes.append(f"FIX STYLE: {style_critique.get('notes', 'style drift')}")
        if not style_critique.get("compositionReadable", True):
            notes.append("FIX COMPOSITION: make the action clearer and more readable")

    if notes:
        return "\n\nCORRECTIONS REQUIRED:\n" + "\n".join(f"- {n}" for n in notes)
    return ""
