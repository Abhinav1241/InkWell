"""
Inkwell — CostGuard  §7.1

The single gate through which every image/video generation must pass.
Implements: mode→model resolution, per-project image cap, spend ledger,
prompt-hash cache, Veo gating, and run cost summary.

⚠️  This file is built FIRST. No image generation code should exist
    that does not route through these functions.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from google.cloud import firestore  # type: ignore[import-untyped]

from backend import config

log = logging.getLogger(__name__)

# ── Firestore client (lazy singleton) ────────────────────────────────────────

_db: firestore.Client | None = None


def _get_db() -> firestore.Client:
    global _db
    if _db is None:
        _db = firestore.Client(project=config.PROJECT_ID or None)
    return _db


# ── Model resolution ─────────────────────────────────────────────────────────


def image_model_for_mode(mode: str | None = None) -> str:
    """Resolve the image model ID for the given cost mode.

    DEV / PREVIEW → cheap model.  FINAL → expensive model.
    The expensive model ID is NEVER hardcoded at a call site.
    """
    m = mode or config.COST_MODE
    if m == config.CostMode.FINAL:
        return config.IMAGE_MODEL_FINAL
    return config.IMAGE_MODEL_DEV


def image_params_for_mode(mode: str | None = None) -> dict[str, Any]:
    """Return image generation parameters tuned for cost.

    DEV  → lowest resolution (512×512 target)
    PREVIEW → normal resolution (1024×1024)
    FINAL → highest quality
    """
    m = mode or config.COST_MODE
    if m == config.CostMode.DEV:
        return {"aspect_ratio": "1:1"}  # smallest practical
    elif m == config.CostMode.PREVIEW:
        return {"aspect_ratio": "3:4"}
    else:  # FINAL
        return {"aspect_ratio": "3:4"}


# ── Per-project image cap ────────────────────────────────────────────────────


def can_generate(project_id: str) -> tuple[bool, str]:
    """Check whether the project is under its image cap.

    Returns (allowed, reason).  When the cap is hit:
    - generation stops
    - project is marked 'capped'
    - a clear trace explains why
    """
    db = _get_db()
    doc = db.collection("projects").document(project_id).get()
    if not doc.exists:
        return False, "Project not found"
    data = doc.to_dict() or {}
    count = data.get("imagesGenerated", 0)
    cap = config.MAX_IMAGES_PER_PROJECT
    if count >= cap:
        # Mark project capped (idempotent)
        db.collection("projects").document(project_id).update({
            "status": "capped",
            "updatedAt": _now(),
        })
        reason = f"Image cap reached: {count}/{cap}. Project capped."
        log.warning(reason)
        return False, reason
    return True, f"{count}/{cap} images used"


# ── Spend ledger ─────────────────────────────────────────────────────────────


def record_generation(
    project_id: str,
    model: str,
    mode: str,
    kind: str = "image",
    panel_id: str | None = None,
    est_cost: float | None = None,
) -> None:
    """Record an image/video generation in the spend ledger.

    Increments imagesGenerated, appends to costs subcollection,
    and updates estSpendUsd on the project doc.
    """
    db = _get_db()
    proj_ref = db.collection("projects").document(project_id)

    # Estimate cost if not provided
    if est_cost is None:
        if kind == "image":
            est_cost = config.EST_COST_PER_IMAGE.get(model, 0.10)
        elif kind == "video":
            est_cost = config.EST_COST_VEO
        else:
            est_cost = 0.05

    # Append cost entry
    proj_ref.collection("costs").add({
        "model": model,
        "mode": mode,
        "kind": kind,
        "estCostUsd": est_cost,
        "panelId": panel_id,
        "ts": _now(),
    })

    # Atomically increment counters on project doc
    proj_ref.update({
        "imagesGenerated": firestore.Increment(1),
        "estSpendUsd": firestore.Increment(est_cost),
        "updatedAt": _now(),
    })

    log.info(
        "CostGuard: recorded %s gen (model=%s, mode=%s, est=$%.3f, panel=%s)",
        kind, model, mode, est_cost, panel_id,
    )


# ── Prompt-hash cache ───────────────────────────────────────────────────────


def prompt_hash(
    prompt: str,
    reference_uris: list[str],
    model: str,
    seed: int | None = None,
) -> str:
    """Compute a deterministic cache key from generation parameters.

    If prompt + refs + model + seed are identical, reuse the existing image.
    """
    payload = json.dumps({
        "prompt": prompt,
        "refs": sorted(reference_uris),
        "model": model,
        "seed": seed,
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def cached_image(project_id: str, phash: str) -> str | None:
    """Return an existing GCS URI if a panel with the same prompt hash exists.

    Checks panels subcollection for a matching promptHash with a completed artUri.
    """
    db = _get_db()
    panels = (
        db.collection("projects")
        .document(project_id)
        .collection("panels")
        .where("promptHash", "==", phash)
        .where("status", "in", ["generated", "approved"])
        .limit(1)
        .get()
    )
    for panel in panels:
        data = panel.to_dict() or {}
        uri = data.get("artUri")
        if uri:
            log.info("CostGuard: cache HIT for hash %s → %s", phash, uri)
            return uri
    return None


# ── Veo gating ───────────────────────────────────────────────────────────────


def veo_enabled(mode: str | None = None) -> bool:
    """Veo video generation is disabled unless COST_MODE == FINAL."""
    m = mode or config.COST_MODE
    return m == config.CostMode.FINAL


# ── Run cost summary ─────────────────────────────────────────────────────────


def run_cost_summary(project_id: str) -> dict[str, Any]:
    """Compute end-of-run cost totals for logging.

    Returns: {totalImages, byModel: {model: count}, estTotalUsd}
    """
    db = _get_db()
    costs = (
        db.collection("projects")
        .document(project_id)
        .collection("costs")
        .get()
    )
    by_model: dict[str, int] = {}
    total_usd = 0.0
    for entry in costs:
        data = entry.to_dict() or {}
        model = data.get("model", "unknown")
        by_model[model] = by_model.get(model, 0) + 1
        total_usd += data.get("estCostUsd", 0.0)

    summary = {
        "totalImages": sum(by_model.values()),
        "byModel": by_model,
        "estTotalUsd": round(total_usd, 4),
    }
    log.info("CostGuard run summary for %s: %s", project_id, summary)
    return summary


# ── Helpers ──────────────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(timezone.utc)
