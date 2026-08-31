"""
Inkwell — Unit Test for Consistency Critic Loop

Specifically tests the self-correction behavior:
1. Panel generated off-model on Iteration 1
2. Vision critic detects drift, emits corrective feedback
3. Panel is re-drawn with corrective notes appended to prompt
4. Vision critic passes on Iteration 2
5. Verifies traces, document status, and iteration count
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


class TestConsistencyCriticLoop(unittest.IsolatedAsyncioTestCase):
    """Verifies that off-model panels trigger corrective re-draws."""

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
    @patch("backend.tools.gemini_vision.build_corrective_notes")
    @patch("backend.tools.pdf.build_pdf")
    async def test_critic_catches_drift_and_redraws(
        self,
        mock_build_pdf,
        mock_build_corrective_notes,
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

        fake_db = FakeFirestoreClient()
        mock_worker_db.return_value = fake_db
        mock_cg_db.return_value = fake_db
        mock_telem_db.return_value = fake_db

        project_id = "test_critic_proj"

        # Seed project
        fake_db.collection("projects").document(project_id).set({
            "status": "intake",
            "costMode": "DEV",
            "title": "Critic Test",
            "options": {"style": "modern comic", "page_count": 1},
            "imagesGenerated": 0,
        })

        # Seed bible core
        fake_db.collection("projects").document(project_id)\
            .collection("bible").document("core").set({
                "premise": "A detective examines a clue.",
                "tone": "noir",
                "setting": "dimly lit office",
            })

        # Seed character
        char_id = "char_vance"
        fake_db.collection("projects").document(project_id)\
            .collection("characters").document(char_id).set({
                "name": "Detective Vance",
                "role": "protagonist",
                "description": "Trench coat, fedora, scarred chin, brown hair",
                "canonicalPromptFragment": "Detective Vance, trench coat, fedora, brown hair",
                "referenceSheetUris": [f"gs://test-bucket/characters/{project_id}/{char_id}/sheet-0.png"],
                "approved": True,
            })

        # Location reference
        mock_generate_location_sheet.return_value = [f"gs://test-bucket/locations/{project_id}/loc_office/sheet-0.png"]

        # Style reference
        mock_generate_style_reference.return_value = f"gs://test-bucket/style/{project_id}/style-ref.png"

        # 1 page, 1 panel
        mock_plan_panels.return_value = {
            "pages": [
                {
                    "index": 0,
                    "panels": [
                        {
                            "order": 0,
                            "shotType": "medium",
                            "staging": "Vance looking at a photograph under desk lamp",
                            "charactersPresent": ["Detective Vance"],
                            "action": "Vance holding a magnifying glass over a photo",
                            "dialogue": [{"speaker": "Detective Vance", "text": "This doesn't add up.", "bubbleType": "speech"}],
                            "caption": "",
                            "beat": "discovery",
                        }
                    ],
                }
            ]
        }

        # Mock image generation: 1 initial draw + 1 corrective re-draw = 2 calls
        mock_generate_panel.side_effect = [
            (f"gs://test-bucket/panels/{project_id}/p1/art_v1.png", "hash_v1"),
            (f"gs://test-bucket/panels/{project_id}/p1/art_v2.png", "hash_v2"),
        ]

        # Vision Critic:
        # Iteration 1: FAIL (hair color drifted to blonde)
        # Iteration 2: PASS
        mock_critique_characters.side_effect = [
            {"results": [{"name": "Detective Vance", "match": False, "note": "Hair drifted to blonde, should be brown"}]},
            {"results": [{"name": "Detective Vance", "match": True, "note": ""}]},
        ]
        mock_critique_locations.return_value = {
            "results": [{"name": "dimly lit office", "match": True, "note": ""}]
        }
        mock_critique_style_readability.return_value = {
            "styleConsistent": True,
            "compositionReadable": True,
            "textOk": None,
            "notes": "",
        }
        mock_all_characters_match.side_effect = [False, True]
        mock_all_locations_match.return_value = True
        mock_build_corrective_notes.return_value = "\n\nCORRECTIONS REQUIRED:\n- FIX Detective Vance: Hair drifted to blonde, should be brown"

        mock_download_bytes.return_value = sample_png
        mock_upload_bytes.side_effect = lambda data, path, **kwargs: f"gs://test-bucket/{path}"
        mock_gcs_path_for.side_effect = lambda kind, pid, *parts: f"{kind}/{pid}/{'/'.join(parts)}"
        mock_build_pdf.return_value = b"%PDF-1.4 sample content"

        # Execute
        result = await run_pipeline(project_id)

        # Verify: generate_panel was called TWICE (initial + re-draw)
        self.assertEqual(mock_generate_panel.call_count, 2)

        # Verify: Second call included the corrective prompt fragment
        second_call_prompt = mock_generate_panel.call_args_list[1][1]["prompt"]
        self.assertIn("CORRECTIONS REQUIRED", second_call_prompt)
        self.assertIn("Hair drifted to blonde", second_call_prompt)

        # Verify: panel ended up approved with criticIterations == 2
        for panel_snap in fake_db.collection("projects").document(project_id).collection("panels").stream():
            p_data = panel_snap.to_dict()
            self.assertEqual(p_data["status"], "approved")
            self.assertEqual(p_data["criticIterations"], 2)

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
    @patch("backend.tools.gemini_vision.build_corrective_notes")
    @patch("backend.tools.pdf.build_pdf")
    async def test_critic_catches_location_drift_and_redraws(
        self,
        mock_build_pdf,
        mock_build_corrective_notes,
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

        fake_db = FakeFirestoreClient()
        mock_worker_db.return_value = fake_db
        mock_cg_db.return_value = fake_db
        mock_telem_db.return_value = fake_db

        project_id = "test_critic_loc_proj"

        # Seed project
        fake_db.collection("projects").document(project_id).set({
            "status": "intake",
            "costMode": "DEV",
            "title": "Location Critic Test",
            "options": {"style": "modern comic", "page_count": 1},
            "imagesGenerated": 0,
        })

        # Seed bible core
        fake_db.collection("projects").document(project_id)\
            .collection("bible").document("core").set({
                "premise": "A keeper tends a lighthouse on storm island.",
                "tone": "mysterious",
                "setting": "Lighthouse Island",
            })

        # Location reference
        mock_generate_location_sheet.return_value = [f"gs://test-bucket/locations/{project_id}/loc_island/sheet-0.png"]
        mock_generate_character_sheet.return_value = []
        mock_generate_style_reference.return_value = f"gs://test-bucket/style/{project_id}/style-ref.png"

        # 1 page, 1 panel
        mock_plan_panels.return_value = {
            "pages": [
                {
                    "index": 0,
                    "panels": [
                        {
                            "order": 0,
                            "shotType": "wide",
                            "staging": "Lighthouse exterior in storm",
                            "charactersPresent": [],
                            "action": "Waves crashing against the lighthouse rocks",
                            "dialogue": [],
                            "caption": "The storm was rising.",
                            "beat": "atmosphere",
                        }
                    ],
                }
            ]
        }

        mock_generate_panel.side_effect = [
            (f"gs://test-bucket/panels/{project_id}/p1/art_v1.png", "hash_v1"),
            (f"gs://test-bucket/panels/{project_id}/p1/art_v2.png", "hash_v2"),
        ]

        # Vision Critic:
        # Iteration 1: FAIL on location (modern city background instead of rocky island)
        # Iteration 2: PASS
        mock_critique_characters.return_value = {"results": []}
        mock_critique_locations.side_effect = [
            {"results": [{"name": "Lighthouse Island", "match": False, "note": "Missing rocky cliffs and lighthouse tower"}]},
            {"results": [{"name": "Lighthouse Island", "match": True, "note": ""}]},
        ]
        mock_critique_style_readability.return_value = {
            "styleConsistent": True,
            "compositionReadable": True,
            "textOk": None,
            "notes": "",
        }
        mock_all_characters_match.return_value = True
        mock_all_locations_match.side_effect = [False, True]
        mock_build_corrective_notes.return_value = "\n\nCORRECTIONS REQUIRED:\n- FIX LOCATION (Lighthouse Island): Missing rocky cliffs and lighthouse tower"

        mock_download_bytes.return_value = sample_png
        mock_upload_bytes.side_effect = lambda data, path, **kwargs: f"gs://test-bucket/{path}"
        mock_gcs_path_for.side_effect = lambda kind, pid, *parts: f"{kind}/{pid}/{'/'.join(parts)}"
        mock_build_pdf.return_value = b"%PDF-1.4 sample content"

        # Execute
        result = await run_pipeline(project_id)

        # Verify: generate_panel called twice
        self.assertEqual(mock_generate_panel.call_count, 2)
        second_call_prompt = mock_generate_panel.call_args_list[1][1]["prompt"]
        self.assertIn("FIX LOCATION", second_call_prompt)
        self.assertIn("Missing rocky cliffs", second_call_prompt)


if __name__ == "__main__":
    unittest.main()
