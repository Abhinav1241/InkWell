"""
Inkwell — Compositor (Lettering + Page Layout)

SVG/Pillow-based compositing for speech bubbles, captions, and page layout.
This is FREE — no model cost. Re-lettering NEVER triggers image regeneration.

Lettering quality features:
  • Bangers font for all-caps speech and dialogue (comic convention)
  • Comic Neue font for narration captions
  • Elliptical speech bubbles with black stroke, white fill, and directional tails
  • Cloud-outline thought bubbles with smooth overlapping lobes and trailing circles
  • Rectangular caption boxes with warm cream fill and dark border
  • Strict panel-bounds clamping: bubbles, tails, clouds, and captions NEVER crop
  • Consistent sizing scaled to panel dimensions
  • Clean separation of dialogue vs captions (no duplicate rendering)
"""

from __future__ import annotations

import io
import logging
import math
import textwrap
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from backend.layouts.templates import LayoutTemplate, template_for

log = logging.getLogger(__name__)

# ── Font paths ───────────────────────────────────────────────────────────────

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"

_FONT_PATHS = {
    "bangers": _ASSETS_DIR / "Bangers-Regular.ttf",
    "comic_neue": _ASSETS_DIR / "ComicNeue-Regular.ttf",
    "comic_neue_bold": _ASSETS_DIR / "ComicNeue-Bold.ttf",
}

# ── Sizing ratios (relative to panel height) ────────────────────────────────

_DIALOGUE_SIZE_RATIO = 0.038      # fraction of panel height -> dialogue font size
_CAPTION_SIZE_RATIO = 0.026       # fraction of panel height -> caption font size
_MIN_FONT_SIZE = 14
_MAX_FONT_SIZE = 36

# ── Bubble styling ──────────────────────────────────────────────────────────

_STROKE_WIDTH = 3                 # black stroke around bubbles
_STROKE_COLOR = (20, 20, 20)
_BUBBLE_FILL = (255, 255, 255)    # opaque white
_TEXT_COLOR = (15, 15, 15)
_CAPTION_FILL = (255, 252, 235)   # warm pale cream
_CAPTION_STROKE = (60, 50, 40)
_CAPTION_TEXT_COLOR = (25, 20, 15)
_THOUGHT_FILL = (255, 255, 255)

# ── Font cache ──────────────────────────────────────────────────────────────

_font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}


def _get_font(name: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a bundled font with caching. Falls back gracefully."""
    key = (name, size)
    if key in _font_cache:
        return _font_cache[key]

    font_path = _FONT_PATHS.get(name)
    if font_path and font_path.exists():
        try:
            font = ImageFont.truetype(str(font_path), size)
            _font_cache[key] = font
            return font
        except Exception as e:
            log.warning("Failed to load %s: %s", font_path, e)

    # Fallback chain: try system fonts, then default
    for system_font in ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf",
                         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        try:
            font = ImageFont.truetype(system_font, size)
            _font_cache[key] = font
            return font
        except (OSError, IOError):
            continue

    font = ImageFont.load_default()
    _font_cache[key] = font
    return font


def _compute_font_size(panel_height: int, ratio: float) -> int:
    """Compute font size scaled to panel, clamped to min/max."""
    return max(_MIN_FONT_SIZE, min(_MAX_FONT_SIZE, int(panel_height * ratio)))


# ── Text measurement ────────────────────────────────────────────────────────

def _measure_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    line_spacing: int = 4,
) -> tuple[int, int, list[tuple[int, int]]]:
    """Measure text block -> (total_width, total_height, [(lw, lh), ...])."""
    sizes = []
    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=font)
        sizes.append((bbox[2] - bbox[0], bbox[3] - bbox[1]))
    total_w = max((s[0] for s in sizes), default=0)
    total_h = sum(s[1] for s in sizes) + max(0, len(sizes) - 1) * line_spacing
    return total_w, total_h, sizes


# ── Elliptical bubble drawing ───────────────────────────────────────────────

def _draw_elliptical_bubble(
    draw: ImageDraw.ImageDraw,
    cx: int, cy: int,
    rx: int, ry: int,
    fill: tuple = _BUBBLE_FILL,
    stroke: tuple = _STROKE_COLOR,
    stroke_width: int = _STROKE_WIDTH,
) -> None:
    """Draw a filled ellipse with black outline — the classic speech bubble."""
    bbox = [cx - rx, cy - ry, cx + rx, cy + ry]
    draw.ellipse(bbox, fill=fill, outline=stroke, width=stroke_width)


def _draw_speech_tail(
    draw: ImageDraw.ImageDraw,
    bubble_cx: int, bubble_cy: int,
    bubble_rx: int, bubble_ry: int,
    target_x: int, target_y: int,
    panel_w: int, panel_h: int,
    margin: int = 16,
    fill: tuple = _BUBBLE_FILL,
    stroke: tuple = _STROKE_COLOR,
    stroke_width: int = _STROKE_WIDTH,
) -> None:
    """Draw a triangular tail from the bubble edge toward the speaker."""
    dx = target_x - bubble_cx
    dy = target_y - bubble_cy
    dist = math.hypot(dx, dy) or 1.0
    nx, ny = dx / dist, dy / dist

    angle = math.atan2(dy, dx)
    edge_x = bubble_cx + int(bubble_rx * math.cos(angle))
    edge_y = bubble_cy + int(bubble_ry * math.sin(angle))

    tail_len = max(16, min(42, int(min(bubble_rx, bubble_ry) * 0.75)))
    tip_x = edge_x + int(nx * tail_len)
    tip_y = edge_y + int(ny * tail_len)

    # Strictly clamp tail tip inside panel bounds
    tip_x = max(margin, min(panel_w - margin, tip_x))
    tip_y = max(margin, min(panel_h - margin, tip_y))

    # Base points on ellipse
    perp_x, perp_y = -ny, nx
    base_spread = max(7, min(16, int(min(bubble_rx, bubble_ry) * 0.28)))
    base1_x = edge_x + int(perp_x * base_spread)
    base1_y = edge_y + int(perp_y * base_spread)
    base2_x = edge_x - int(perp_x * base_spread)
    base2_y = edge_y - int(perp_y * base_spread)

    draw.polygon(
        [(base1_x, base1_y), (tip_x, tip_y), (base2_x, base2_y)],
        fill=fill,
    )
    draw.line([(base1_x, base1_y), (tip_x, tip_y)], fill=stroke, width=stroke_width)
    draw.line([(tip_x, tip_y), (base2_x, base2_y)], fill=stroke, width=stroke_width)


# ── Thought bubble drawing (organic cloud shape) ───────────────────────────

def _draw_thought_bubble(
    draw: ImageDraw.ImageDraw,
    cx: int, cy: int,
    rx: int, ry: int,
    target_x: int, target_y: int,
    panel_w: int, panel_h: int,
    margin: int = 16,
    fill: tuple = _THOUGHT_FILL,
    stroke: tuple = _STROKE_COLOR,
    stroke_width: int = _STROKE_WIDTH,
) -> None:
    """Draw a comic cloud thought bubble with varied overlapping lobes and trailing circles."""
    n_lobes = 10
    base_r = max(12, int(min(rx, ry) * 0.42))
    lobes = []
    for i in range(n_lobes):
        ang = 2 * math.pi * i / n_lobes
        lr = base_r * (1.1 + 0.25 * math.sin(ang * 3 + 0.5))
        lx = cx + (rx - 4) * math.cos(ang)
        ly = cy + (ry - 4) * math.sin(ang)
        lobes.append((lx, ly, lr))

    # 1. Draw outer lobes with stroke
    for lx, ly, lr in lobes:
        draw.ellipse(
            [lx - lr, ly - lr, lx + lr, ly + lr],
            fill=fill, outline=stroke, width=stroke_width,
        )

    # 2. Fill interior with solid white to cover internal lobe stroke seams
    draw.ellipse([cx - rx + 4, cy - ry + 4, cx + rx - 4, cy + ry - 4], fill=fill)
    for lx, ly, lr in lobes:
        draw.ellipse([lx - lr + 2, ly - lr + 2, lx + lr - 2, ly + lr - 2], fill=fill)

    # 3. Trailing circles toward the thinker
    dx = target_x - cx
    dy = target_y - cy
    dist = math.hypot(dx, dy) or 1.0
    nx, ny = dx / dist, dy / dist

    angle = math.atan2(dy, dx)
    start_x = cx + rx * math.cos(angle)
    start_y = cy + ry * math.sin(angle)

    for j, (cr, dist_off) in enumerate([(9, 18), (6, 36), (4, 50)]):
        ccx = start_x + nx * dist_off
        ccy = start_y + ny * dist_off
        ccx = max(margin, min(panel_w - margin, ccx))
        ccy = max(margin, min(panel_h - margin, ccy))
        draw.ellipse(
            [ccx - cr, ccy - cr, ccx + cr, ccy + cr],
            fill=fill, outline=stroke, width=max(1, stroke_width - 1),
        )


# ── Caption box drawing ─────────────────────────────────────────────────────

def _draw_caption_box(
    draw: ImageDraw.ImageDraw,
    x: int, y: int, w: int, h: int,
    fill: tuple = _CAPTION_FILL,
    stroke: tuple = _CAPTION_STROKE,
    stroke_width: int = 2,
) -> None:
    """Draw a rectangular caption box with crisp edges."""
    draw.rectangle([x, y, x + w, y + h], fill=fill, outline=stroke, width=stroke_width)


# ── Speaker position estimation ─────────────────────────────────────────────

def _estimate_speaker_pos(
    panel_w: int,
    panel_h: int,
    speaker_index: int,
    total_speakers: int,
    staging: str = "",
) -> tuple[int, int]:
    """Estimate speaker position in the lower portion of the panel."""
    staging_lower = staging.lower() if staging else ""

    if "left" in staging_lower:
        sx = int(panel_w * 0.28)
    elif "right" in staging_lower:
        sx = int(panel_w * 0.72)
    elif total_speakers > 1:
        segment = panel_w / (total_speakers + 1)
        sx = int(segment * (speaker_index + 1))
    else:
        sx = panel_w // 2

    sy = int(panel_h * 0.72)
    return sx, sy


# ═══════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def letter_panel(
    art_bytes: bytes,
    dialogue: list[dict],
    caption: str = "",
    staging: str = "",
) -> bytes:
    """Overlay speech bubbles and captions on panel art.

    Args:
        art_bytes: PNG bytes of the panel art.
        dialogue: [{speaker, text, bubbleType/bubble_type}]
        caption: Narration caption text.
        staging: Staging description (hints for speaker positions).

    Returns:
        PNG bytes of the lettered panel.
    """
    img = Image.open(io.BytesIO(art_bytes)).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    w, h = img.size
    margin = max(18, int(min(w, h) * 0.025))

    # Compute font sizes scaled to panel height
    dialogue_size = _compute_font_size(h, _DIALOGUE_SIZE_RATIO)
    caption_size = _compute_font_size(h, _CAPTION_SIZE_RATIO)

    speech_font = _get_font("bangers", dialogue_size)
    caption_font = _get_font("comic_neue", caption_size)

    # ── 1. Separate Speech/Thought Bubbles vs Captions ─────────────────────────
    bubble_items: list[tuple[str, str]] = []  # [(text, type)]
    caption_items: list[str] = []

    # Process dialogue lines
    for d in dialogue:
        raw_text = d.get("text", "").strip()
        if not raw_text:
            continue
        raw_type = d.get("bubbleType") or d.get("bubble_type") or "speech"
        b_type = str(raw_type).lower().strip()

        if b_type == "caption":
            if raw_text not in caption_items:
                caption_items.append(raw_text)
        elif b_type == "thought":
            bubble_items.append((raw_text, "thought"))
        else:
            bubble_items.append((raw_text, "speech"))

    # Add standalone caption if present and not already added
    if caption and caption.strip():
        cap_clean = caption.strip()
        if cap_clean not in caption_items:
            caption_items.append(cap_clean)

    n_bubbles = len(bubble_items)

    # ── 2. Render Speech & Thought Bubbles ───────────────────────────────────
    for bubble_idx, (raw_text, bubble_type) in enumerate(bubble_items):
        # ALL-CAPS for speech and thought bubbles per comic convention
        text = raw_text.upper()

        # Wrap text to fit in ~36% of panel width
        max_chars = max(12, int((w * 0.36) / (dialogue_size * 0.55)))
        wrapped = textwrap.fill(text, width=max_chars)
        lines = wrapped.split("\n")

        # Measure text block
        text_w, text_h, line_sizes = _measure_lines(draw, lines, speech_font, line_spacing=4)

        # Generous elliptical bubble radii to ensure text corners never poke out
        rx = max(35, int(text_w * 0.42 + 24))
        ry = max(24, int(text_h * 0.45 + 18))

        # Estimate speaker position
        speaker_x, speaker_y = _estimate_speaker_pos(
            w, h, bubble_idx, n_bubbles, staging
        )

        # Initial bubble placement
        if n_bubbles == 1:
            initial_cx = speaker_x
        elif bubble_idx % 2 == 0:
            initial_cx = max(margin + rx, int(w * 0.32))
        else:
            initial_cx = min(w - margin - rx, int(w * 0.68))

        # Vertical placement: top area with stagger
        stagger_y = bubble_idx * (ry * 2 + 16)
        initial_cy = margin + ry + 8 + stagger_y

        # If bubble would overlap the speaker vertically, adjust
        if initial_cy + ry + 20 > speaker_y:
            initial_cy = max(margin + ry, speaker_y - ry - 35)

        # ── STRICT BOUNDS CLAMPING (Never crop at panel edge) ────────────────
        cx = max(margin + rx, min(w - margin - rx, initial_cx))
        cy = max(margin + ry, min(h - margin - ry, initial_cy))

        target_x = speaker_x
        target_y = speaker_y

        if bubble_type == "thought":
            _draw_thought_bubble(
                draw, cx, cy, rx, ry,
                target_x, target_y,
                panel_w=w, panel_h=h,
                margin=margin,
            )
        else:
            _draw_elliptical_bubble(draw, cx, cy, rx, ry)
            _draw_speech_tail(
                draw, cx, cy, rx, ry,
                target_x, target_y,
                panel_w=w, panel_h=h,
                margin=margin,
            )

        # Draw centered text
        ty = cy - text_h // 2
        for ln, (lw, lh) in zip(lines, line_sizes):
            tx = cx - lw // 2
            draw.text((tx, ty), ln, fill=_TEXT_COLOR, font=speech_font)
            ty += lh + 4

    # ── 3. Render Caption Boxes ──────────────────────────────────────────────
    for cap_idx, cap_text in enumerate(caption_items):
        max_caption_chars = max(18, int((w * 0.46) / (caption_size * 0.52)))
        wrapped_cap = textwrap.fill(cap_text, width=max_caption_chars)
        cap_lines = wrapped_cap.split("\n")

        cap_text_w, cap_text_h, cap_line_sizes = _measure_lines(
            draw, cap_lines, caption_font, line_spacing=3
        )

        pad_x = 14
        pad_y = 10
        cap_w = cap_text_w + pad_x * 2
        cap_h = cap_text_h + pad_y * 2

        # Placement: top-left if no speech bubbles; bottom-left if bubbles present
        if n_bubbles == 0:
            init_cx = margin
            init_cy = margin + cap_idx * (cap_h + 10)
        else:
            init_cx = margin
            init_cy = h - cap_h - margin - cap_idx * (cap_h + 10)

        # Strict clamping within panel bounds
        cap_x = max(margin, min(w - cap_w - margin, init_cx))
        cap_y = max(margin, min(h - cap_h - margin, init_cy))

        _draw_caption_box(draw, cap_x, cap_y, cap_w, cap_h)

        # Draw caption text inside box
        ty = cap_y + pad_y
        for ln, (lw, lh) in zip(cap_lines, cap_line_sizes):
            draw.text((cap_x + pad_x, ty), ln, fill=_CAPTION_TEXT_COLOR, font=caption_font)
            ty += lh + 3

    # Composite overlay onto art
    result = Image.alpha_composite(img, overlay).convert("RGB")

    buf = io.BytesIO()
    result.save(buf, format="PNG", quality=95)
    return buf.getvalue()


def compose_page(
    lettered_panels: list[bytes],
    template: Optional[LayoutTemplate] = None,
    page_width: int = 1200,
    page_height: int = 1600,
    bg_color: tuple[int, int, int] = (245, 240, 235),
    border_color: tuple[int, int, int] = (30, 30, 30),
) -> bytes:
    """Arrange lettered panels into a page layout using a template.

    Args:
        lettered_panels: List of PNG bytes (one per panel), in reading order.
        template: Layout template (auto-selected by panel count if None).
        page_width: Output page width in pixels.
        page_height: Output page height in pixels.
        bg_color: Page background color.
        border_color: Panel border color.

    Returns:
        PNG bytes of the composed page.
    """
    if template is None:
        template = template_for(len(lettered_panels))

    page = Image.new("RGB", (page_width, page_height), bg_color)
    draw = ImageDraw.Draw(page)

    border = int(page_width * template.border)
    gutter = int(page_width * template.gutter)

    # Usable area after borders
    area_x = border
    area_y = border
    area_w = page_width - 2 * border
    area_h = page_height - 2 * border

    for i, panel_rect in enumerate(template.panels):
        if i >= len(lettered_panels):
            break

        # Calculate pixel coordinates within the usable area
        px = area_x + int(panel_rect.x * area_w)
        py = area_y + int(panel_rect.y * area_h)
        pw = int(panel_rect.w * area_w) - gutter
        ph = int(panel_rect.h * area_h) - gutter

        # Load and resize panel
        panel_img = Image.open(io.BytesIO(lettered_panels[i]))
        panel_img = panel_img.resize((pw, ph), Image.Resampling.LANCZOS)

        # Draw border
        draw.rectangle(
            [px - 2, py - 2, px + pw + 2, py + ph + 2],
            outline=border_color,
            width=2,
        )

        # Paste panel
        page.paste(panel_img, (px, py))

    buf = io.BytesIO()
    page.save(buf, format="PNG", quality=95)
    return buf.getvalue()
