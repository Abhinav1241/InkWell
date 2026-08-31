"""
Inkwell — PDF Export

Assemble page images into a downloadable PDF.
Uses reportlab for simplicity and reliability.
"""

from __future__ import annotations

import io
import logging

from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

log = logging.getLogger(__name__)


def build_pdf(page_images: list[bytes], title: str = "Inkwell Comic") -> bytes:
    """Assemble page images into a PDF.

    Args:
        page_images: List of PNG bytes, one per page.
        title: PDF title metadata.

    Returns:
        PDF file as bytes.
    """
    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=letter)
    pdf.setTitle(title)

    page_w, page_h = letter  # 612 x 792 points

    for i, img_bytes in enumerate(page_images):
        if i > 0:
            pdf.showPage()

        # Load image to get dimensions
        img = Image.open(io.BytesIO(img_bytes))
        img_w, img_h = img.size

        # Scale to fit page while maintaining aspect ratio
        scale = min(page_w / img_w, page_h / img_h)
        draw_w = img_w * scale
        draw_h = img_h * scale

        # Center on page
        x = (page_w - draw_w) / 2
        y = (page_h - draw_h) / 2

        pdf.drawImage(
            ImageReader(io.BytesIO(img_bytes)),
            x, y, draw_w, draw_h,
        )

    pdf.save()
    return buf.getvalue()
