import tempfile
import unittest
from unittest.mock import patch

from pydantic import ValidationError

import config.app_config as app_config
from config.app_config import RuntimeConfig


class RuntimeConfigTests(unittest.TestCase):
    def test_settings_are_saved_and_loaded_from_data_directory(self):
        with tempfile.TemporaryDirectory() as data_dir:
            with (
                patch.object(app_config.settings, "DATA_DIR", data_dir),
                patch.object(app_config, "_runtime_config", None),
            ):
                saved = app_config.update_runtime_config(RuntimeConfig(
                    ollama_host="http://localhost:11434/",
                    ollama_model="llama3.2",
                    temperature=0.5,
                    max_tokens=1024,
                ))
                self.assertEqual(saved.ollama_host, "http://localhost:11434")

                with patch.object(app_config, "_runtime_config", None):
                    loaded = app_config.get_runtime_config()
                self.assertEqual(loaded, saved)

    def test_default_host_is_not_pinned_by_saved_settings(self):
        with tempfile.TemporaryDirectory() as data_dir:
            with (
                patch.object(app_config.settings, "DATA_DIR", data_dir),
                patch.object(app_config.settings, "OLLAMA_HOST", "http://host.docker.internal:11434"),
                patch.object(app_config, "_runtime_config", None),
            ):
                app_config.update_runtime_config(RuntimeConfig(
                    ollama_host="http://host.docker.internal:11434",
                    ollama_model="llama3.2",
                ))
            with (
                patch.object(app_config.settings, "DATA_DIR", data_dir),
                patch.object(app_config.settings, "OLLAMA_HOST", "http://localhost:11434"),
                patch.object(app_config, "_runtime_config", None),
            ):
                self.assertEqual(app_config.get_runtime_config().ollama_host, "http://localhost:11434")

    def test_rejects_host_credentials_and_invalid_inference_values(self):
        with self.assertRaises(ValidationError):
            RuntimeConfig(ollama_host="http://user:pass@localhost:11434", ollama_model="model")
        with self.assertRaises(ValidationError):
            RuntimeConfig(
                ollama_host="http://localhost:11434",
                ollama_model="model",
                max_tokens=0,
            )


if __name__ == "__main__":
    unittest.main()
