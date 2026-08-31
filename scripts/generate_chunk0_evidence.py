"""
Inkwell — Chunk 0 Evidence Generator

Renders visual evidence for Chunk 0:
1. Real milestone Page 1 re-lettered end-to-end (letter_panel -> compose_page)
2. Real milestone Page 2 re-lettered end-to-end (letter_panel -> compose_page)
3. Speech bubbles (Bangers, all-caps, directional tails, proper bounds)
4. Thought bubble (organic cloud lobes, trailing circles)
5. Caption box (Comic Neue, warm cream fill, crisp border)
6. Mixed panel (speech + thought + caption)

⚠️ Zero image generation calls — uses existing art only.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image
from backend.tools.compositor import letter_panel, compose_page
from backend.layouts.templates import template_for

EVIDENCE_DIR = ROOT / "docs" / "chunk_0_evidence"
MILESTONE_DIR = ROOT / "milestone_day2_verified"


def _heal_box(img: Image.Image, target_box: tuple[int, int, int, int], source_box: tuple[int, int, int, int]) -> Image.Image:
    """Heal a region by cloning texture from an adjacent region."""
    img = img.copy()
    x1, y1, x2, y2 = target_box
    sx1, sy1, sx2, sy2 = source_box
    w, h = x2 - x1, y2 - y1
    patch = img.crop((sx1, sy1, sx1 + w, sy1 + h))
    img.paste(patch, (x1, y1))
    return img


def generate_milestone_page1():
    """Extract panels from milestone Page 1, letter with upgraded compositor, compose page."""
    print("Generating milestone Page 1 evidence...")
    page1_src = Image.open(MILESTONE_DIR / "page_1.png")
    
    # Extract panels: stacked_2 layout on 1200x1600 (border=36, gutter=24)
    p1_art = page1_src.crop((36, 36, 1140, 760))
    p2_art = page1_src.crop((36, 815, 1140, 1539))
    
    # Clean old Day 2 bubbles (x=420..660, y=0..85) using clean left wood/metal texture
    p1_art = _heal_box(p1_art, (400, 0, 680, 85), (100, 0, 380, 85))
    p2_art = _heal_box(p2_art, (400, 0, 680, 85), (100, 0, 380, 85))
    
    buf1, buf2 = io.BytesIO(), io.BytesIO()
    p1_art.save(buf1, format="PNG")
    p2_art.save(buf2, format="PNG")
    
    # Panel 1: Speech + Caption
    panel1_lettered = letter_panel(
        buf1.getvalue(),
        dialogue=[{"speaker": "Elara", "text": "Another fierce one...", "bubbleType": "speech"}],
        caption="The lighthouse keeper watches the storm.",
        staging="Elara on the right, facing workbench",
    )
    
    # Panel 2: Speech
    panel2_lettered = letter_panel(
        buf2.getvalue(),
        dialogue=[{"speaker": "Elara", "text": "No! Not now!", "bubbleType": "speech"}],
        caption="",
        staging="Elara hand reaching from bottom-right",
    )
    
    # Compose Page 1
    page1_composed = compose_page([panel1_lettered, panel2_lettered], template=template_for(2))
    
    # Save output
    p1_out = Image.open(io.BytesIO(page1_composed))
    p1_out.save(EVIDENCE_DIR / "milestone_page_1.png")
    p1_out.save(EVIDENCE_DIR / "milestone_lettered.png")  # alias for review
    print("  ✓ Saved milestone_page_1.png (and milestone_lettered.png)")


def generate_milestone_page2():
    """Extract panels from milestone Page 2, letter with upgraded compositor, compose page."""
    print("Generating milestone Page 2 evidence...")
    page2_src = Image.open(MILESTONE_DIR / "page_2.png")
    
    # Extract panels: t_layout_3 layout on 1200x1600 (border=36, gutter=24)
    p1_art = page2_src.crop((36, 36, 1140, 745))
    p2_art = page2_src.crop((36, 800, 564, 1540))
    p3_art = page2_src.crop((611, 800, 1139, 1540))
    
    # Clean old Day 2 boxes without source overlap
    # Panel 1 old box was at x=340..780. Source: clean sky from x=20..280
    p1_art = _heal_box(p1_art, (320, 0, 560, 90), (30, 0, 270, 90))
    p1_art = _heal_box(p1_art, (560, 0, 800, 90), (30, 0, 270, 90))
    
    # Panel 2 old caption was at bottom-left x=0..140, y=675..735. Source: clean wave x=160..300
    p2_art = _heal_box(p2_art, (0, 670, 140, 735), (160, 670, 300, 735))
    
    # Panel 3 old box was at x=180..380. Source: clean sky from x=10..210
    p3_art = _heal_box(p3_art, (170, 0, 380, 85), (0, 0, 210, 85))
    
    buf1, buf2, buf3 = io.BytesIO(), io.BytesIO(), io.BytesIO()
    p1_art.save(buf1, format="PNG")
    p2_art.save(buf2, format="PNG")
    p3_art.save(buf3, format="PNG")
    
    # Panel 1: Narration Caption (NO speech bubble)
    p1_lettered = letter_panel(
        buf1.getvalue(),
        dialogue=[],
        caption="The mechanism was at the top, exposed to the worst of the tempest.",
        staging="Elara center on catwalk",
    )
    
    # Panel 2: Scene-setting Caption
    p2_lettered = letter_panel(
        buf2.getvalue(),
        dialogue=[],
        caption="The deep stirs...",
        staging="Lighthouse left, sea creature bottom",
    )
    
    # Panel 3: Thought Bubble (NO speech tail)
    p3_lettered = letter_panel(
        buf3.getvalue(),
        dialogue=[{"speaker": "Elara", "text": "This isn't... just the storm.", "bubbleType": "thought"}],
        caption="",
        staging="Elara on the right examining broken glass",
    )
    
    # Compose Page 2
    page2_composed = compose_page([p1_lettered, p2_lettered, p3_lettered], template=template_for(3))
    
    p2_out = Image.open(io.BytesIO(page2_composed))
    p2_out.save(EVIDENCE_DIR / "milestone_page_2.png")
    print("  ✓ Saved milestone_page_2.png")


def generate_isolated_fixtures():
    """Generate isolated visual verification samples."""
    print("Generating isolated fixture evidence...")
    
    def make_canvas(w=600, h=800, color=(65, 75, 90)):
        img = Image.new("RGB", (w, h), color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    
    # 1. Speech bubbles
    sb_art = make_canvas()
    sb_bytes = letter_panel(
        sb_art,
        dialogue=[
            {"speaker": "Elara", "text": "Another fierce one...", "bubbleType": "speech"},
            {"speaker": "Elara", "text": "No! Not now!", "bubbleType": "speech"},
        ],
        staging="Elara on left, facing right",
    )
    Image.open(io.BytesIO(sb_bytes)).save(EVIDENCE_DIR / "speech_bubbles.png")
    print("  ✓ Saved speech_bubbles.png")
    
    # 2. Thought bubble
    tb_art = make_canvas()
    tb_bytes = letter_panel(
        tb_art,
        dialogue=[{"speaker": "Elara", "text": "What if it's too late...", "bubbleType": "thought"}],
        staging="Elara center",
    )
    Image.open(io.BytesIO(tb_bytes)).save(EVIDENCE_DIR / "thought_bubble.png")
    print("  ✓ Saved thought_bubble.png")
    
    # 3. Caption box
    cb_art = make_canvas()
    cb_bytes = letter_panel(
        cb_art,
        dialogue=[],
        caption="The deep stirs...",
    )
    Image.open(io.BytesIO(cb_bytes)).save(EVIDENCE_DIR / "caption_box.png")
    print("  ✓ Saved caption_box.png")
    
    # 4. Mixed panel
    mp_art = make_canvas()
    mp_bytes = letter_panel(
        mp_art,
        dialogue=[
            {"speaker": "Elara", "text": "The mechanism was exposed to the tempest.", "bubbleType": "speech"},
            {"speaker": "Elara", "text": "This isn't just the storm.", "bubbleType": "thought"},
        ],
        caption="The deep stirs...",
        staging="Elara on the right",
    )
    Image.open(io.BytesIO(mp_bytes)).save(EVIDENCE_DIR / "mixed_panel.png")
    print("  ✓ Saved mixed_panel.png")


def main():
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating Chunk 0 evidence in {EVIDENCE_DIR}...\n")
    
    generate_milestone_page1()
    generate_milestone_page2()
    generate_isolated_fixtures()
    
    print("\n✅ All Chunk 0 evidence generated successfully.")


if __name__ == "__main__":
    main()
