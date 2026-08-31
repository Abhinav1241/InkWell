"""
Inkwell — Unit Tests for CostGuard

Tests mode resolution, cap logic, hash computation, and Veo gating.
⚠️ No image generation calls — uses mocks only.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from backend import config
from backend.tools import cost_guard


class TestModelResolution(unittest.TestCase):
    """image_model_for_mode must resolve correctly per cost mode."""

    def test_dev_returns_cheap_model(self):
        result = cost_guard.image_model_for_mode("DEV")
        self.assertEqual(result, config.IMAGE_MODEL_DEV)

    def test_preview_returns_cheap_model(self):
        result = cost_guard.image_model_for_mode("PREVIEW")
        self.assertEqual(result, config.IMAGE_MODEL_DEV)

    def test_final_returns_expensive_model(self):
        result = cost_guard.image_model_for_mode("FINAL")
        self.assertEqual(result, config.IMAGE_MODEL_FINAL)

    def test_default_is_never_final(self):
        """COST_MODE defaults to DEV — never FINAL."""
        result = cost_guard.image_model_for_mode()
        self.assertNotEqual(result, config.IMAGE_MODEL_FINAL)


class TestImageParams(unittest.TestCase):
    """image_params_for_mode must return cost-appropriate settings."""

    def test_dev_params(self):
        params = cost_guard.image_params_for_mode("DEV")
        self.assertEqual(params["aspect_ratio"], "1:1")

    def test_preview_params(self):
        params = cost_guard.image_params_for_mode("PREVIEW")
        self.assertEqual(params["aspect_ratio"], "3:4")

    def test_final_params(self):
        params = cost_guard.image_params_for_mode("FINAL")
        self.assertEqual(params["aspect_ratio"], "3:4")


class TestPromptHash(unittest.TestCase):
    """prompt_hash must be deterministic and change when inputs change."""

    def test_same_inputs_same_hash(self):
        h1 = cost_guard.prompt_hash("draw a cat", ["gs://a.png"], "model-a", 42)
        h2 = cost_guard.prompt_hash("draw a cat", ["gs://a.png"], "model-a", 42)
        self.assertEqual(h1, h2)

    def test_different_prompt_different_hash(self):
        h1 = cost_guard.prompt_hash("draw a cat", ["gs://a.png"], "model-a")
        h2 = cost_guard.prompt_hash("draw a dog", ["gs://a.png"], "model-a")
        self.assertNotEqual(h1, h2)

    def test_different_refs_different_hash(self):
        h1 = cost_guard.prompt_hash("prompt", ["gs://a.png"], "m")
        h2 = cost_guard.prompt_hash("prompt", ["gs://b.png"], "m")
        self.assertNotEqual(h1, h2)

    def test_ref_order_irrelevant(self):
        """References are sorted, so order doesn't matter."""
        h1 = cost_guard.prompt_hash("prompt", ["gs://b.png", "gs://a.png"], "m")
        h2 = cost_guard.prompt_hash("prompt", ["gs://a.png", "gs://b.png"], "m")
        self.assertEqual(h1, h2)


class TestVeoGating(unittest.TestCase):
    """Veo must be disabled outside FINAL mode."""

    def test_dev_disabled(self):
        self.assertFalse(cost_guard.veo_enabled("DEV"))

    def test_preview_disabled(self):
        self.assertFalse(cost_guard.veo_enabled("PREVIEW"))

    def test_final_enabled(self):
        self.assertTrue(cost_guard.veo_enabled("FINAL"))


class TestCriticIters(unittest.TestCase):
    """Critic iteration caps must match spec."""

    def test_dev_is_2(self):
        self.assertEqual(config.max_critic_iters("DEV"), 2)

    def test_preview_is_2(self):
        self.assertEqual(config.max_critic_iters("PREVIEW"), 2)

    def test_final_is_3(self):
        self.assertEqual(config.max_critic_iters("FINAL"), 3)


class TestSheetImageModel(unittest.TestCase):
    """Character sheets use Pro model in FINAL mode."""

    def test_dev_uses_dev_model(self):
        self.assertEqual(config.sheet_image_model("DEV"), config.IMAGE_MODEL_DEV)

    def test_final_uses_final_model(self):
        self.assertEqual(config.sheet_image_model("FINAL"), config.IMAGE_MODEL_FINAL)


class TestCanGenerate(unittest.TestCase):
    """can_generate must check image cap correctly."""

    @patch.object(cost_guard, '_get_db')
    def test_under_cap_allowed(self, mock_get_db):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"imagesGenerated": 5}
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        ok, reason = cost_guard.can_generate("test-project")
        self.assertTrue(ok)
        self.assertIn("5/40", reason)

    @patch.object(cost_guard, '_get_db')
    def test_at_cap_blocked(self, mock_get_db):
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"imagesGenerated": 40}
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        ok, reason = cost_guard.can_generate("test-project")
        self.assertFalse(ok)
        self.assertIn("cap reached", reason.lower())


if __name__ == "__main__":
    unittest.main()
