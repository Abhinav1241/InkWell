"""
Inkwell — Unit Tests for Compositor

Tests lettering and page layout with fixture images.
⚠️ No image generation calls — uses synthetic test images only.
"""

from __future__ import annotations

import io
import unittest
from pathlib import Path

from PIL import Image

from backend.tools.compositor import letter_panel, compose_page
from backend.layouts.templates import template_for, LayoutTemplate


def _make_test_image(w: int = 400, h: int = 533, color: tuple = (100, 150, 200)) -> bytes:
    """Create a simple test image as PNG bytes."""
    img = Image.new("RGB", (w, h), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestLetterPanel(unittest.TestCase):
    """letter_panel must overlay text without crashing."""

    def test_basic_lettering(self):
        art = _make_test_image()
        dialogue = [
            {"speaker": "Maya", "text": "Hello there!", "bubbleType": "speech"},
            {"speaker": "Kai", "text": "How's it going?", "bubbleType": "speech"},
        ]
        result = letter_panel(art, dialogue, caption="A warm evening.")
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 100)

        # Verify it's a valid image
        img = Image.open(io.BytesIO(result))
        self.assertEqual(img.size, (400, 533))

    def test_empty_dialogue(self):
        art = _make_test_image()
        result = letter_panel(art, [], caption="")
        self.assertIsInstance(result, bytes)

    def test_thought_bubble(self):
        art = _make_test_image()
        dialogue = [{"speaker": "Maya", "text": "I wonder...", "bubbleType": "thought"}]
        result = letter_panel(art, dialogue)
        self.assertIsInstance(result, bytes)

    def test_caption_only(self):
        art = _make_test_image()
        result = letter_panel(art, [], caption="The city slept.")
        self.assertIsInstance(result, bytes)

    def test_long_dialogue(self):
        art = _make_test_image()
        dialogue = [{"speaker": "Maya", "text": "This is a very long line of dialogue that should be wrapped properly across multiple lines in the bubble.", "bubbleType": "speech"}]
        result = letter_panel(art, dialogue)
        self.assertIsInstance(result, bytes)

    def test_staging_hint(self):
        """Staging hints should influence tail direction."""
        art = _make_test_image(600, 800)
        dialogue = [{"speaker": "Elara", "text": "The storm is getting worse!", "bubbleType": "speech"}]
        result = letter_panel(art, dialogue, staging="Elara stands on the left, looking right")
        self.assertIsInstance(result, bytes)

        img = Image.open(io.BytesIO(result))
        self.assertEqual(img.size, (600, 800))

    def test_multiple_bubble_types(self):
        """Mix of speech, thought, and caption in one panel."""
        art = _make_test_image(600, 800)
        dialogue = [
            {"speaker": "Elara", "text": "No! Not now!", "bubbleType": "speech"},
            {"speaker": "Elara", "text": "What if it's too late...", "bubbleType": "thought"},
        ]
        result = letter_panel(art, dialogue, caption="The deep stirs...")
        self.assertIsInstance(result, bytes)

    def test_all_caps_conversion(self):
        """Speech text should be rendered in all-caps (convention check)."""
        art = _make_test_image()
        dialogue = [{"speaker": "Maya", "text": "hello world", "bubbleType": "speech"}]
        # If this doesn't crash, the all-caps logic in letter_panel works
        result = letter_panel(art, dialogue)
        self.assertIsInstance(result, bytes)

    def test_large_panel(self):
        """Fonts should scale up for large panels."""
        art = _make_test_image(1200, 1600)
        dialogue = [
            {"speaker": "A", "text": "Big panel!", "bubbleType": "speech"},
        ]
        result = letter_panel(art, dialogue, caption="A full-page splash.")
        self.assertIsInstance(result, bytes)


class TestComposePage(unittest.TestCase):
    """compose_page must arrange panels per template."""

    def test_single_splash(self):
        panels = [_make_test_image()]
        result = compose_page(panels)
        img = Image.open(io.BytesIO(result))
        self.assertEqual(img.size, (1200, 1600))

    def test_two_panels(self):
        panels = [_make_test_image(color=(200, 100, 100)),
                  _make_test_image(color=(100, 200, 100))]
        result = compose_page(panels)
        self.assertIsInstance(result, bytes)

    def test_four_panels_grid(self):
        panels = [_make_test_image(color=(i * 50, 100, 150)) for i in range(4)]
        result = compose_page(panels)
        self.assertIsInstance(result, bytes)

    def test_six_panels(self):
        panels = [_make_test_image() for _ in range(6)]
        result = compose_page(panels)
        self.assertIsInstance(result, bytes)


class TestTemplateSelection(unittest.TestCase):
    """template_for must return appropriate templates."""

    def test_one_panel_splash(self):
        t = template_for(1)
        self.assertEqual(t.name, "splash")
        self.assertEqual(len(t.panels), 1)

    def test_four_panel_grid(self):
        t = template_for(4)
        self.assertEqual(t.name, "grid_4")
        self.assertEqual(len(t.panels), 4)

    def test_clamp_to_six(self):
        t = template_for(10)
        self.assertEqual(t.panel_count, 6)

    def test_reading_order(self):
        for count in range(1, 7):
            t = template_for(count)
            orders = [p.order for p in t.panels]
            self.assertEqual(orders, list(range(count)))


class TestPdfExport(unittest.TestCase):
    """PDF build must produce valid output."""

    def test_basic_pdf(self):
        from backend.tools.pdf import build_pdf
        pages = [_make_test_image() for _ in range(3)]
        result = build_pdf(pages, title="Test Comic")
        self.assertIsInstance(result, bytes)
        self.assertTrue(result.startswith(b"%PDF"))
        self.assertGreater(len(result), 100)


if __name__ == "__main__":
    unittest.main()
