"""
Inkwell — Visual Lettering Test

Tests the upgraded compositor against real panel art from milestone_day2_verified/.
Outputs lettered results to tests/fixtures/lettering_output/ for visual inspection.

⚠️ Zero image regeneration — uses existing panel images only.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image
from backend.tools.compositor import letter_panel, compose_page

OUTPUT_DIR = Path(__file__).parent / "fixtures" / "lettering_output"
MILESTONE_DIR = Path(__file__).resolve().parent.parent / "milestone_day2_verified"


def _create_sample_panel(w: int = 600, h: int = 800) -> bytes:
    """Create a sample panel for testing when milestone images aren't panels."""
    img = Image.new("RGB", (w, h), (80, 90, 100))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_speech_bubbles():
    """Test speech bubble rendering with multiple speakers."""
    print("  Testing speech bubbles...")
    art = _create_sample_panel()
    dialogue = [
        {"speaker": "Elara", "text": "Another fierce one...", "bubbleType": "speech"},
        {"speaker": "Narrator", "text": "No! Not now!", "bubbleType": "speech"},
    ]
    result = letter_panel(art, dialogue, caption="", staging="Elara on left, facing right")
    img = Image.open(io.BytesIO(result))
    img.save(OUTPUT_DIR / "test_speech_bubbles.png")
    print(f"    ✓ Saved ({img.size[0]}×{img.size[1]})")


def test_thought_bubble():
    """Test thought bubble with cloud outline and trailing circles."""
    print("  Testing thought bubbles...")
    art = _create_sample_panel()
    dialogue = [
        {"speaker": "Elara", "text": "What if it's too late...", "bubbleType": "thought"},
    ]
    result = letter_panel(art, dialogue, staging="Elara center")
    img = Image.open(io.BytesIO(result))
    img.save(OUTPUT_DIR / "test_thought_bubble.png")
    print(f"    ✓ Saved ({img.size[0]}×{img.size[1]})")


def test_caption_box():
    """Test caption box rendering."""
    print("  Testing caption boxes...")
    art = _create_sample_panel()
    result = letter_panel(art, [], caption="The deep stirs...")
    img = Image.open(io.BytesIO(result))
    img.save(OUTPUT_DIR / "test_caption_only.png")
    print(f"    ✓ Saved ({img.size[0]}×{img.size[1]})")


def test_mixed_panel():
    """Test a panel with speech, thought, and caption."""
    print("  Testing mixed panel (speech + thought + caption)...")
    art = _create_sample_panel()
    dialogue = [
        {"speaker": "Elara", "text": "The mechanism was at the top, exposed to the worst of the tempest.", "bubbleType": "speech"},
        {"speaker": "Elara", "text": "This isn't just the storm.", "bubbleType": "thought"},
    ]
    result = letter_panel(art, dialogue, caption="The deep stirs...", staging="Elara on right")
    img = Image.open(io.BytesIO(result))
    img.save(OUTPUT_DIR / "test_mixed_panel.png")
    print(f"    ✓ Saved ({img.size[0]}×{img.size[1]})")


def test_with_milestone_images():
    """Test lettering on actual milestone page images if available."""
    print("  Testing with milestone images...")

    page1 = MILESTONE_DIR / "page_1.png"
    if not page1.exists():
        print("    ⚠ milestone_day2_verified/page_1.png not found, skipping")
        return

    # Load the full page and crop out individual panels for testing
    page_img = Image.open(page1)
    pw, ph = page_img.size
    print(f"    Page 1 size: {pw}×{ph}")

    # Simulate lettering on the full page as a single "panel"
    buf = io.BytesIO()
    page_img.save(buf, format="PNG")
    art_bytes = buf.getvalue()

    dialogue = [
        {"speaker": "Elara", "text": "Another fierce one...", "bubbleType": "speech"},
    ]
    result = letter_panel(art_bytes, dialogue, caption="The lighthouse keeper watches the storm.",
                          staging="Elara center")
    img = Image.open(io.BytesIO(result))
    img.save(OUTPUT_DIR / "test_milestone_page1_lettered.png")
    print(f"    ✓ Saved milestone test ({img.size[0]}×{img.size[1]})")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Lettering visual test -- output -> {OUTPUT_DIR}\n")

    test_speech_bubbles()
    test_thought_bubble()
    test_caption_box()
    test_mixed_panel()
    test_with_milestone_images()

    print(f"\n✅ All visual tests complete. Check {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
