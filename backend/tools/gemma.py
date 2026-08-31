"""
Inkwell — Gemma Tool (Complexity Triage & Content Moderation)

Uses Gemma when configured and accessible via API.
Per user instruction: We test genuine Gemma calls; if unavailable or unconfigured,
we gracefully return default values without attempting to fake Gemma with other models.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from backend import config

log = logging.getLogger(__name__)

_client = None
_gemma_available: bool | None = None


def is_gemma_available() -> bool:
    """Check if a genuine Gemma model is callable."""
    global _gemma_available, _client
    if _gemma_available is not None:
        return _gemma_available

    try:
        from google import genai
        if _client is None:
            _client = genai.Client(
                project=config.PROJECT_ID or None,
                location=config.REGION or None,
            )
        # Probe gemma
        _client.models.generate_content(
            model=config.GEMMA_MODEL,
            contents="ping",
        )
        _gemma_available = True
        log.info("Genuine Gemma model (%s) is available", config.GEMMA_MODEL)
    except Exception as e:
        _gemma_available = False
        log.info("Gemma model (%s) not directly reachable: %s. Continuing with default triage.", config.GEMMA_MODEL, e)

    return _gemma_available


def triage_panel(panel_meta: dict[str, Any]) -> dict[str, Any]:
    """Triage panel complexity and whether draft pass is needed.

    Returns: {"complexity": "SIMPLE" | "COMPLEX", "useDraft": bool}
    """
    if not is_gemma_available():
        # Fallback default heuristic: simple shot with 1 or 0 chars is SIMPLE
        n_chars = len(panel_meta.get("charactersPresent", []))
        shot = panel_meta.get("shotType", "medium")
        if n_chars <= 1 and shot in ("close", "medium"):
            return {"complexity": "SIMPLE", "useDraft": False}
        return {"complexity": "COMPLEX", "useDraft": True}

    from backend.prompts.prompts import P_GEMMA_TRIAGE
    prompt = P_GEMMA_TRIAGE.format(
        shot_type=panel_meta.get("shotType", "medium"),
        n_chars=len(panel_meta.get("charactersPresent", [])),
        has_dialogue=bool(panel_meta.get("dialogue")),
        action=panel_meta.get("action", "")[:100],
    )

    try:
        response = _client.models.generate_content(
            model=config.GEMMA_MODEL,
            contents=prompt,
        )
        text = response.text or "{}"
        return json.loads(text)
    except Exception as e:
        log.warning("Gemma triage call failed: %s", e)
        return {"complexity": "COMPLEX", "useDraft": True}


def moderate(prompt: str, rating: str = "all-ages") -> bool:
    """Check prompt for content safety."""
    if not is_gemma_available():
        return True  # Default allow

    from backend.prompts.prompts import P_GEMMA_MODERATE
    p = P_GEMMA_MODERATE.format(rating=rating, prompt=prompt[:200])
    try:
        response = _client.models.generate_content(
            model=config.GEMMA_MODEL,
            contents=p,
        )
        data = json.loads(response.text or "{}")
        return data.get("safe", True)
    except Exception:
        return True
