"""
Inkwell — Integration Tests for Worker Pipeline

Tests the full linear pipeline end-to-end with FakeFirestore and mocks for:
GCS (storage), Gemini Image, Gemini Text, and Gemini Vision.
Verifies phase transitions, document updates, critic loop, lettering, layout, and export.
⚠️ NEVER calls live APIs.
"""

from __future__ import annotations

import io
import unittest
from unittest.mock import MagicMock, patch

from PIL import Image

from tests.fake_firestore import FakeFirestoreClient


def _make_png_bytes(color=(100, 150, 200), size=(400, 533)) -> bytes:
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestWorkerPipelineMocked(unittest.IsolatedAsyncioTestCase):
    """End-to-end test of the worker pipeline using FakeFirestore and tool mocks."""

    @patch("backend.telemetry._get_db")
    @patch("backend.tools.cost_guard._get_db")
    @patch("backend.worker._get_db")
    @patch("backend.tools.storage.download_bytes")
    @patch("backend.tools.storage.upload_bytes")
    @patch("backend.tools.storage.gcs_path_for")
    @patch("backend.tools.gemini_image.generate_character_sheet")
    @patch("backend.tools.gemini_image.generate_location_sheet")
    @patch("backend.tools.gemini_image.generate_style_reference")
    @patch("backend.tools.gemini_image.generate_panel")
    @patch("backend.tools.gemini_text.plan_panels")
    @patch("backend.tools.gemini_vision.critique_characters")
    @patch("backend.tools.gemini_vision.critique_locations")
    @patch("backend.tools.gemini_vision.critique_style_readability")
    @patch("backend.tools.gemini_vision.all_characters_match")
    @patch("backend.tools.gemini_vision.all_locations_match")
    @patch("backend.tools.pdf.build_pdf")
    async def test_full_pipeline_2_pages_1_character(
        self,
        mock_build_pdf,
        mock_all_locations_match,
        mock_all_characters_match,
        mock_critique_style_readability,
        mock_critique_locations,
        mock_critique_characters,
        mock_plan_panels,
        mock_generate_panel,
        mock_generate_style_reference,
        mock_generate_location_sheet,
        mock_generate_character_sheet,
        mock_gcs_path_for,
        mock_upload_bytes,
        mock_download_bytes,
        mock_worker_db,
        mock_cg_db,
        mock_telem_db,
    ):
        from backend.worker import run_pipeline

        sample_png = _make_png_bytes()

        # 1. Setup Fake Firestore
        fake_db = FakeFirestoreClient()
        mock_worker_db.return_value = fake_db
        mock_cg_db.return_value = fake_db
        mock_telem_db.return_value = fake_db

        project_id = "test_project_123"

        # Seed project document
        fake_db.collection("projects").document(project_id).set({
            "status": "intake",
            "costMode": "DEV",
            "title": "The Last Lighthouse Keeper",
            "options": {
                "style": "manga-influenced modern comic",
                "page_count": 2,
                "rating": "all-ages",
            },
            "imagesGenerated": 0,
        })

        # Seed bible core
        fake_db.collection("projects").document(project_id)\
            .collection("bible").document("core").set({
                "premise": "An old lighthouse keeper tends a light sealing a dark creature.",
                "tone": "mysterious and atmospheric",
                "setting": "isolated lighthouse island",
            })

        # Seed character
        char_id = "char_elara"
        fake_db.collection("projects").document(project_id)\
            .collection("characters").document(char_id).set({
                "name": "Elara",
                "role": "protagonist",
                "description": "Elderly woman, 60s, weathered face, gray braid, knit sweater",
                "canonicalPromptFragment": "Elara, elderly woman, weathered face, gray braid",
                "referenceSheetUris": [],
                "approved": False,
            })

        # 2. Setup Mock Gemini Tools
        mock_generate_character_sheet.return_value = [
            f"gs://test-bucket/characters/{project_id}/{char_id}/sheet-0.png"
        ]
        mock_generate_location_sheet.return_value = [
            f"gs://test-bucket/locations/{project_id}/loc_lighthouse/sheet-0.png"
        ]
        mock_generate_style_reference.return_value = (
            f"gs://test-bucket/style/{project_id}/style-ref.png"
        )
        mock_generate_panel.side_effect = [
            (f"gs://test-bucket/panels/{project_id}/p1/art.png", "hash_p1"),
            (f"gs://test-bucket/panels/{project_id}/p2/art.png", "hash_p2"),
        ]

        mock_plan_panels.return_value = {
            "pages": [
                {
                    "index": 0,
                    "panels": [
                        {
                            "order": 0,
                            "shotType": "wide",
                            "staging": "Lighthouse on rocky cliff in storm",
                            "charactersPresent": ["Elara"],
                            "action": "Elara climbing the stairs holding a brass lantern",
                            "dialogue": [{"speaker": "Elara", "text": "Hold steady...", "bubbleType": "speech"}],
                            "caption": "The storm had breached the reef.",
                            "beat": "tension",
                        }
                    ],
                },
                {
                    "index": 1,
                    "panels": [
                        {
                            "order": 0,
                            "shotType": "close",
                            "staging": "Elara staring into the storm",
                            "charactersPresent": ["Elara"],
                            "action": "Elara gasping as shadows rise from the water",
                            "dialogue": [{"speaker": "Elara", "text": "It's awake.", "bubbleType": "speech"}],
                            "caption": "",
                            "beat": "climax",
                        }
                    ],
                },
            ]
        }

        # Vision critic verdicts: pass on first iteration
        mock_critique_characters.return_value = {
            "results": [{"name": "Elara", "match": True, "note": ""}]
        }
        mock_critique_locations.return_value = {
            "results": [{"name": "isolated lighthouse island", "match": True, "note": ""}]
        }
        mock_critique_style_readability.return_value = {
            "styleConsistent": True,
            "compositionReadable": True,
            "textOk": None,
            "notes": "",
        }
        mock_all_characters_match.return_value = True
        mock_all_locations_match.return_value = True

        # Storage mock
        mock_download_bytes.return_value = sample_png
        mock_upload_bytes.side_effect = lambda data, path, **kwargs: f"gs://test-bucket/{path}"
        mock_gcs_path_for.side_effect = lambda kind, pid, *parts: f"{kind}/{pid}/{'/'.join(parts)}"

        # PDF mock
        mock_build_pdf.return_value = b"%PDF-1.4 sample content"

        # 3. Run Pipeline
        result = await run_pipeline(project_id)

        # 4. Assertions
        self.assertIsNotNone(result)
        self.assertIn("pdfUri", result)
        self.assertIn("readerManifestUri", result)
        self.assertTrue(mock_generate_character_sheet.called)
        self.assertTrue(mock_generate_location_sheet.called)
        self.assertTrue(mock_plan_panels.called)
        self.assertEqual(mock_generate_panel.call_count, 2)
        self.assertTrue(mock_build_pdf.called)

        # Check final project doc in FakeFirestore
        proj_snap = fake_db.collection("projects").document(project_id).get()
        self.assertEqual(proj_snap.to_dict()["status"], "done")
        self.assertEqual(proj_snap.to_dict()["progress"], 100)


if __name__ == "__main__":
    unittest.main()
