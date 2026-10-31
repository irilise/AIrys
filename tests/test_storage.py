import json
import tempfile
import unittest
from pathlib import Path

from backend.memory.storage import FileStorage


class FileStorageTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.storage = FileStorage(
            conversations_dir=str(root / "conversations"),
            data_dir=str(root / "data"),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_conversation_round_trip_and_clear(self):
        self.storage.save_conversation("active_session", "Hello", "Hi there")

        conversation = self.storage.get_conversation("active_session")
        self.assertEqual(len(conversation["sessions"]), 1)
        self.assertEqual(conversation["sessions"][0]["user_message"], "Hello")
        self.assertEqual(conversation["sessions"][0]["response"], "Hi there")
        self.storage.clear_conversation("active_session")
        self.assertIsNone(self.storage.get_conversation("active_session"))

    def test_memory_metadata_round_trip_and_category_listing(self):
        self.storage.save_memory("first", "I prefer tea", "preference", 123.0)
        self.storage.save_memory("second", "Dentist on Friday", "reminder", 456.0)

        self.assertEqual(self.storage.get_memory("first"), (
            "I prefer tea",
            {"category": "preference", "created_at": 123.0},
        ))
        self.assertEqual(self.storage.get_all_memory_ids(), ["first", "second"])
        self.assertEqual(self.storage.get_memory_ids_by_category("reminder"), ["second"])
        self.assertEqual(self.storage.get_memory_categories(), ["preference", "reminder"])

        self.storage.delete_memory("first")
        self.assertEqual(self.storage.get_all_memory_ids(), ["second"])
        self.storage.clear_all_memories()
        self.assertEqual(self.storage.get_all_memory_ids(), [])

    def test_metadata_is_valid_json(self):
        metadata_path = Path(self.temp_dir.name) / "conversations" / "memories_metadata.json"
        self.storage.save_memory("memory-id", "remember this")
        self.assertEqual(json.loads(metadata_path.read_text())["memories"]["memory-id"]["content"], "remember this")


if __name__ == "__main__":
    unittest.main()
