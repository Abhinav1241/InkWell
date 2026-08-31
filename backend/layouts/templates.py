"""
Inkwell — Page Layout Templates (§13)

Fixed templates per panel count for reliable reading order and clean gutters.
Each template defines panel rectangles as normalized (0–1) coordinates
within the page area, plus gutter and border sizes.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PanelRect:
    """A panel rectangle in normalized coordinates (0–1)."""
    x: float      # left edge
    y: float      # top edge
    w: float      # width
    h: float      # height
    order: int     # reading order (0-based)


@dataclass
class LayoutTemplate:
    """A page layout template for a given number of panels."""
    name: str
    panel_count: int
    panels: list[PanelRect] = field(default_factory=list)
    gutter: float = 0.02       # fraction of page width
    border: float = 0.03       # fraction of page width
    page_width: int = 1200     # pixels
    page_height: int = 1600    # pixels (3:4 aspect)


def _g(gutter: float = 0.02, border: float = 0.03) -> tuple[float, float]:
    return gutter, border


# ── Templates ────────────────────────────────────────────────────────────────

def _splash() -> LayoutTemplate:
    """1 panel: full-page splash."""
    return LayoutTemplate(
        name="splash",
        panel_count=1,
        panels=[PanelRect(0, 0, 1.0, 1.0, 0)],
    )


def _stacked_2() -> LayoutTemplate:
    """2 panels: stacked vertically (50/50)."""
    g = 0.02
    h = (1.0 - g) / 2
    return LayoutTemplate(
        name="stacked_2",
        panel_count=2,
        panels=[
            PanelRect(0, 0, 1.0, h, 0),
            PanelRect(0, h + g, 1.0, h, 1),
        ],
    )


def _t_layout_3() -> LayoutTemplate:
    """3 panels: one wide on top, two on the bottom."""
    g = 0.02
    top_h = 0.48
    bot_h = 1.0 - top_h - g
    half_w = (1.0 - g) / 2
    return LayoutTemplate(
        name="t_layout_3",
        panel_count=3,
        panels=[
            PanelRect(0, 0, 1.0, top_h, 0),
            PanelRect(0, top_h + g, half_w, bot_h, 1),
            PanelRect(half_w + g, top_h + g, half_w, bot_h, 2),
        ],
    )


def _grid_4() -> LayoutTemplate:
    """4 panels: 2×2 grid."""
    g = 0.02
    half_w = (1.0 - g) / 2
    half_h = (1.0 - g) / 2
    return LayoutTemplate(
        name="grid_4",
        panel_count=4,
        panels=[
            PanelRect(0, 0, half_w, half_h, 0),
            PanelRect(half_w + g, 0, half_w, half_h, 1),
            PanelRect(0, half_h + g, half_w, half_h, 2),
            PanelRect(half_w + g, half_h + g, half_w, half_h, 3),
        ],
    )


def _magazine_5() -> LayoutTemplate:
    """5 panels: top row of 2, middle splash, bottom row of 2."""
    g = 0.02
    row_h = 0.30
    mid_h = 1.0 - 2 * row_h - 2 * g
    half_w = (1.0 - g) / 2
    return LayoutTemplate(
        name="magazine_5",
        panel_count=5,
        panels=[
            PanelRect(0, 0, half_w, row_h, 0),
            PanelRect(half_w + g, 0, half_w, row_h, 1),
            PanelRect(0, row_h + g, 1.0, mid_h, 2),
            PanelRect(0, row_h + g + mid_h + g, half_w, row_h, 3),
            PanelRect(half_w + g, row_h + g + mid_h + g, half_w, row_h, 4),
        ],
    )


def _magazine_6() -> LayoutTemplate:
    """6 panels: 3 rows × 2 columns."""
    g = 0.02
    half_w = (1.0 - g) / 2
    third_h = (1.0 - 2 * g) / 3
    return LayoutTemplate(
        name="magazine_6",
        panel_count=6,
        panels=[
            PanelRect(0, 0, half_w, third_h, 0),
            PanelRect(half_w + g, 0, half_w, third_h, 1),
            PanelRect(0, third_h + g, half_w, third_h, 2),
            PanelRect(half_w + g, third_h + g, half_w, third_h, 3),
            PanelRect(0, 2 * (third_h + g), half_w, third_h, 4),
            PanelRect(half_w + g, 2 * (third_h + g), half_w, third_h, 5),
        ],
    )


# ── Template registry ───────────────────────────────────────────────────────

_TEMPLATES: dict[int, LayoutTemplate] = {
    1: _splash(),
    2: _stacked_2(),
    3: _t_layout_3(),
    4: _grid_4(),
    5: _magazine_5(),
    6: _magazine_6(),
}


def template_for(panel_count: int) -> LayoutTemplate:
    """Select a layout template by panel count.

    Clamps to 1–6. If count > 6, uses the 6-panel template
    (extra panels would need to overflow to the next page).
    """
    clamped = max(1, min(panel_count, 6))
    return _TEMPLATES[clamped]
