"""
Inkwell — Gemini Text Tool (gemini-3.5-flash)

All text-only reasoning: story extraction, clarifying questions,
panel planning, dialogue polish. Uses structured JSON output.
"""

from __future__ import annotations

import json
import logging
import re
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
    """Extract JSON from a model response, handling markdown fences."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
    cleaned = re.sub(r"\n?```\s*$", "", cleaned)
    return json.loads(cleaned)


import time


def _generate_json(prompt: str, max_retries: int = 3) -> Any:
    """Call gemini-3.5-flash and parse the JSON response.

    Retries on malformed JSON or 429 rate limits with exponential backoff.
    """
    client = _get_client()
    last_error: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=config.TEXT_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.7 if attempt == 0 else 0.5,
                ),
            )
            text = response.text or ""
            return _parse_json(text)
        except Exception as e:
            last_error = e
            err_str = str(e)
            is_429 = (
                "429" in err_str
                or "RESOURCE_EXHAUSTED" in err_str
                or "ResourceExhausted" in err_str
                or "Too Many Requests" in err_str
            )
            if is_429 and attempt < max_retries:
                backoff = 4.0 * (2 ** attempt)
                log.warning(
                    "Gemini Text rate-limited (429). Retrying in %.1fs (attempt %d/%d)...",
                    backoff,
                    attempt + 1,
                    max_retries,
                )
                time.sleep(backoff)
                continue
            elif isinstance(e, (json.JSONDecodeError, ValueError)):
                log.warning(
                    "JSON parse failed (attempt %d/%d): %s",
                    attempt + 1, max_retries + 1, e,
                )
                if attempt < max_retries:
                    prompt = prompt + "\n\nIMPORTANT: Return ONLY valid JSON. No markdown fences or extra text."
            else:
                raise

    raise ValueError(f"Failed to parse JSON after {max_retries + 1} attempts: {last_error}")


# ── Public API ───────────────────────────────────────────────────────────────

def extract_story(raw_story: str) -> dict[str, Any]:
    """P1: Extract premise, characters, tone from raw story input.

    Returns: {logline, tone, setting, characters: [...], questions: [...]}
    """
    from backend.prompts.prompts import P1_INTAKE
    prompt = P1_INTAKE.format(raw_story=raw_story)
    result = _generate_json(prompt)
    log.info("Extracted story: logline=%s, %d chars, %d questions",
             result.get("logline", "")[:60],
             len(result.get("characters", [])),
             len(result.get("questions", [])))
    return result


def clarifying_questions(bible: dict[str, Any]) -> list[str]:
    """Generate follow-up clarifying questions based on current bible state."""
    prompt = (
        "Based on this Story Bible, generate 2-3 additional clarifying questions "
        "that would help refine the comic's visual direction. Focus on art style, "
        "mood, pacing, and character design details that are still ambiguous.\n\n"
        f"Bible: {json.dumps(bible, indent=2)}\n\n"
        "Return JSON: [\"question1\", \"question2\", ...]"
    )
    return _generate_json(prompt)


def plan_panels(bible: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
    """P3: Break story into pages and panels.

    Returns: {pages: [{index, panels: [{order, shotType, staging, ...}]}]}
    """
    from backend.prompts.prompts import P3_PANEL_PLAN
    target_page_count = int(options.get("pageCount") or options.get("page_count") or config.DEFAULT_PAGES)
    prompt = P3_PANEL_PLAN.format(
        page_count=target_page_count,
        page_count_minus_1=max(0, target_page_count - 1),
        style_phrase=options.get("style", "modern comic"),
        rating=options.get("rating", "all-ages"),
        bible_json=json.dumps(bible, indent=2),
    )
    result = _generate_json(prompt)
    pages = result.get("pages", [])

    # Hard clamp to target_page_count to protect budget
    if len(pages) > target_page_count:
        log.warning(
            "plan_panels: LLM returned %d pages; hard clamping to %d pages",
            len(pages),
            target_page_count,
        )
        pages = pages[:target_page_count]
        result["pages"] = pages

    total_panels = sum(len(p.get("panels", [])) for p in pages)
    log.info("Panel plan: %d pages, %d total panels", len(pages), total_panels)
    return result


def polish_dialogue(dialogue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """P6: Tighten dialogue for comic bubbles."""
    from backend.prompts.prompts import P6_DIALOGUE_POLISH
    prompt = P6_DIALOGUE_POLISH.format(
        dialogue_json=json.dumps(dialogue, indent=2),
    )
    return _generate_json(prompt)


def apply_answers(bible: dict[str, Any], answers: dict[str, str]) -> dict[str, Any]:
    """Apply user's answers to clarifying questions to mutate the bible.

    Uses Gemini to intelligently merge the answers into the bible.
    """
    prompt = (
        "You are updating a Story Bible for a comic based on the author's answers "
        "to clarifying questions. Merge the answers into the existing bible, "
        "updating tone, style, pacing, character details, etc. as needed.\n\n"
        f"Current Bible: {json.dumps(bible, indent=2)}\n\n"
        f"Author's Answers: {json.dumps(answers, indent=2)}\n\n"
        "Return the COMPLETE updated bible as JSON (same schema as the input, "
        "with modifications applied)."
    )
    return _generate_json(prompt)
