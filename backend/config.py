"""
Inkwell — Central Configuration

All model IDs, cost controls, and infrastructure config loaded from environment.
COST_MODE defaults to DEV. The expensive model is NEVER the default.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)

# ── Google Cloud ──────────────────────────────────────────────────────────────

PROJECT_ID: str = (
    os.getenv("PROJECT_ID")
    or os.getenv("GCP_PROJECT")
    or os.getenv("GOOGLE_CLOUD_PROJECT")
    or "gen-lang-client-0795624280"
)
REGION: str = os.getenv("REGION", "us-central1")
VERTEX_LOCATION: str = os.getenv("VERTEX_LOCATION", "global")
ASSETS_BUCKET: str = os.getenv("ASSETS_BUCKET", "")
JOBS_TOPIC: str = os.getenv("JOBS_TOPIC", "inkwell-jobs")

# ── Models (Vertex AI) ───────────────────────────────────────────────────────

TEXT_MODEL: str = os.getenv("TEXT_MODEL", "gemini-3.5-flash")
IMAGE_MODEL_DEV: str = os.getenv("IMAGE_MODEL_DEV", "gemini-2.5-flash-image")
IMAGE_MODEL_FINAL: str = os.getenv("IMAGE_MODEL_FINAL", "gemini-3-pro-image")
VEO_MODEL: str = os.getenv("VEO_MODEL", "veo-3.1-generate-001")
GEMMA_MODEL: str = os.getenv("GEMMA_MODEL", "gemma-3-4b-it")
TTS_VOICE: str = os.getenv("TTS_VOICE", "en-US-Chirp3-HD-Puck")

# ── Cost Controls ─────────────────────────────────────────────────────────────

class CostMode:
    DEV = "DEV"
    PREVIEW = "PREVIEW"
    FINAL = "FINAL"

COST_MODE: str = os.getenv("COST_MODE", CostMode.DEV)  # ⚠️ NEVER default to FINAL

MAX_IMAGES_PER_PROJECT: int = int(os.getenv("MAX_IMAGES_PER_PROJECT", "40"))

# Critic iteration caps (per spec: DEV=2, PREVIEW=2, FINAL=3)
MAX_CRITIC_ITERS: dict[str, int] = {
    CostMode.DEV: int(os.getenv("MAX_CRITIC_ITERS_DEV", "2")),
    CostMode.PREVIEW: int(os.getenv("MAX_CRITIC_ITERS_PREVIEW", "2")),
    CostMode.FINAL: int(os.getenv("MAX_CRITIC_ITERS_FINAL", "3")),
}

PARALLEL_PANELS: int = int(os.getenv("PARALLEL_PANELS", "3"))
MAX_MAIN_CHARACTERS: int = int(os.getenv("MAX_MAIN_CHARACTERS", "3"))
DEFAULT_PAGES: int = int(os.getenv("DEFAULT_PAGES", "6"))

# ── Local Dev ─────────────────────────────────────────────────────────────────

LOCAL_DEV: bool = os.getenv("LOCAL_DEV", "false").lower() == "true"

# ── Estimated costs per image (USD) for the spend ledger ─────────────────────

EST_COST_PER_IMAGE: dict[str, float] = {
    IMAGE_MODEL_DEV: 0.045,
    IMAGE_MODEL_FINAL: 0.24,
    "gemini-2.5-flash-image": 0.045,
    "gemini-3.1-flash-image": 0.045,
    "gemini-3-pro-image": 0.24,
}
EST_COST_VEO: float = 0.50  # rough estimate for a short clip


def max_critic_iters(mode: str | None = None) -> int:
    """Return the critic iteration cap for the given (or current) cost mode."""
    m = mode or COST_MODE
    return MAX_CRITIC_ITERS.get(m, 2)


def sheet_image_model(mode: str | None = None) -> str:
    """Character sheets use the Pro model in FINAL mode (per spec amendment)."""
    m = mode or COST_MODE
    if m == CostMode.FINAL:
        return IMAGE_MODEL_FINAL
    return IMAGE_MODEL_DEV
