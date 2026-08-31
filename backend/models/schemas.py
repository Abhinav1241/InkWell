"""
Inkwell — Pydantic Data Models (§9)

Matches the Firestore document schemas. Used for API request/response
validation and for type-safe internal data passing.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────────────────────────

class ProjectStatus(str, Enum):
    INTAKE = "intake"
    DESIGNING = "designing"
    PLANNING = "planning"
    DRAWING = "drawing"
    LETTERING = "lettering"
    LAYING_OUT = "laying_out"
    EXPORTING = "exporting"
    DONE = "done"
    CAPPED = "capped"
    ERROR = "error"


class PanelStatus(str, Enum):
    PENDING = "pending"
    DRAFTED = "drafted"
    GENERATED = "generated"
    APPROVED = "approved"
    NEEDS_REVIEW = "needs_review"
    FAILED = "failed"
    SKIPPED_CAPPED = "skipped_capped"


class BubbleType(str, Enum):
    SPEECH = "speech"
    THOUGHT = "thought"
    CAPTION = "caption"


class ContentRating(str, Enum):
    ALL_AGES = "all-ages"
    TEEN = "teen"
    MATURE = "mature"


class ShotType(str, Enum):
    WIDE = "wide"
    MEDIUM = "medium"
    CLOSE = "close"
    SPLASH = "splash"


# ── Sub-models ───────────────────────────────────────────────────────────────

class DialogueLine(BaseModel):
    speaker: Optional[str] = None
    text: str
    bubble_type: BubbleType = BubbleType.SPEECH


class ProjectOptions(BaseModel):
    style: str = "manga-influenced modern comic"
    page_count: int = 6
    rating: ContentRating = ContentRating.ALL_AGES
    aspect: str = "3:4"
    palette: str = "vibrant"
    pacing: str = "balanced"


class ProjectResult(BaseModel):
    reader_manifest_uri: Optional[str] = None
    pdf_uri: Optional[str] = None
    bible_json_uri: Optional[str] = None
    motion_uri: Optional[str] = None


# ── Top-level documents ──────────────────────────────────────────────────────

class Character(BaseModel):
    """projects/{projectId}/characters/{charId}"""
    id: str = ""
    name: str
    role: str = "supporting"
    description: str = ""
    canonical_prompt_fragment: str = ""
    reference_sheet_uris: list[str] = Field(default_factory=list)
    traits: dict[str, str] = Field(default_factory=dict)
    approved: bool = False
    first_appearance_page: int = 0


class Location(BaseModel):
    """projects/{projectId}/locations/{locId}"""
    id: str = ""
    name: str
    description: str = ""
    canonical_prompt_fragment: str = ""
    reference_sheet_uris: list[str] = Field(default_factory=list)
    traits: dict[str, str] = Field(default_factory=dict)
    approved: bool = False


class StyleGuide(BaseModel):
    """projects/{projectId}/bible/style"""
    description: str = ""
    style_reference_uris: list[str] = Field(default_factory=list)
    palette: str = ""
    canonical_style_phrase: str = ""


class Panel(BaseModel):
    """projects/{projectId}/panels/{panelId}"""
    id: str = ""
    page_index: int = 0
    order: int = 0
    shot_type: ShotType = ShotType.MEDIUM
    staging: str = ""
    characters_present: list[str] = Field(default_factory=list)
    action: str = ""
    caption: str = ""
    dialogue: list[DialogueLine] = Field(default_factory=list)
    draft_uri: Optional[str] = None
    art_uri: Optional[str] = None
    lettered_uri: Optional[str] = None
    prompt_hash: Optional[str] = None
    status: PanelStatus = PanelStatus.PENDING
    critic_iterations: int = 0
    critic_notes: list[str] = Field(default_factory=list)


class Page(BaseModel):
    """projects/{projectId}/pages/{pageId}"""
    id: str = ""
    index: int = 0
    layout_template: str = "grid"
    panel_ids: list[str] = Field(default_factory=list)
    page_image_uri: Optional[str] = None
    status: str = "pending"


class Message(BaseModel):
    """projects/{projectId}/messages/{msgId}"""
    role: str = "user"  # "user" | "agent"
    text: str = ""
    ts: Optional[datetime] = None
    data: Optional[dict[str, Any]] = None


class CostEntry(BaseModel):
    """projects/{projectId}/costs/{entryId}"""
    model: str = ""
    mode: str = ""
    kind: str = "image"  # "image" | "video"
    est_cost_usd: float = 0.0
    panel_id: Optional[str] = None
    ts: Optional[datetime] = None


class TraceEntry(BaseModel):
    """projects/{projectId}/traces/{traceId}"""
    ts: Optional[datetime] = None
    stage: str = ""
    level: str = "info"  # "info" | "decision" | "warn"
    message: str = ""
    data: Optional[dict[str, Any]] = None


class Project(BaseModel):
    """projects/{projectId}"""
    id: str = ""
    status: ProjectStatus = ProjectStatus.INTAKE
    progress: int = 0
    title: str = ""
    logline: str = ""
    options: ProjectOptions = Field(default_factory=ProjectOptions)
    cost_mode: str = "DEV"
    images_generated: int = 0
    est_spend_usd: float = 0.0
    result: Optional[ProjectResult] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    error: Optional[str] = None


# ── API models ───────────────────────────────────────────────────────────────

class CreateProjectRequest(BaseModel):
    story: str = ""
    title: str = ""


class TurnRequest(BaseModel):
    text: str


class ApproveRequest(BaseModel):
    target: str  # "character" | "panel"
    id: str
    decision: str  # "approve" | "reject"
    note: str = ""
