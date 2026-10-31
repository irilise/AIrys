import unittest
from unittest.mock import patch

import smoke_test


class SmokeTestHelpersTests(unittest.TestCase):
    def test_selects_configured_installed_model(self):
        models = [
            {"name": "small:latest", "size": 10, "capabilities": ["completion"]},
            {"name": "preferred:latest", "size": 100, "capabilities": ["completion"]},
        ]
        self.assertEqual(
            smoke_test.find_model(models, "preferred"),
            models[1],
        )

    def test_selects_smallest_chat_model_not_embedding_only_model(self):
        models = [
            {"name": "embedding:latest", "size": 1, "capabilities": ["embedding"]},
            {"name": "large:latest", "size": 100, "capabilities": ["completion"]},
            {"name": "small:latest", "size": 10, "capabilities": ["completion"]},
        ]
        self.assertEqual(
            smoke_test.find_model(models, "not-installed"),
            models[2],
        )

    def test_pulls_fallback_model_when_ollama_has_no_chat_model(self):
        fallback = {"name": smoke_test.FALLBACK_MODEL, "size": 1, "capabilities": ["completion"]}
        with (
            patch.object(smoke_test, "ollama_tags", side_effect=[[], [fallback]]),
            patch.object(smoke_test, "pull_model") as pull_model,
        ):
            self.assertEqual(
                smoke_test.ensure_local_model("not-installed"),
                smoke_test.FALLBACK_MODEL,
            )
        pull_model.assert_called_once_with(smoke_test.FALLBACK_MODEL)

    def test_collects_frontend_vite_assets(self):
        parser = smoke_test.AssetParser()
        parser.feed(
            '<script type="module" src="/@vite/client"></script>'
            '<script type="module" src="/src/main.jsx"></script>'
            '<link rel="stylesheet" href="/assets/index.css">'
        )
        self.assertEqual(
            parser.assets,
            ["/@vite/client", "/src/main.jsx", "/assets/index.css"],
        )


if __name__ == "__main__":
    unittest.main()
