import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from backend.server import app
from api import chat_routes, memory_routes, settings_routes
from config.app_config import RuntimeConfig
from memory.storage import FileStorage


class FakeVectorDatabase:
    def __init__(self):
        self.records = {}

    def create_embedding(self, _content):
        return [1.0, 0.0]

    def add(self, ids, documents, metadatas, **_kwargs):
        for memory_id, document, metadata in zip(ids, documents, metadatas):
            self.records[memory_id] = {"text": document, "metadata": metadata}

    def search(self, query, n_results, min_similarity):
        return [
            {"id": memory_id, **record, "score": 0.9}
            for memory_id, record in list(self.records.items())[:n_results]
        ]

    def delete(self, ids):
        for memory_id in ids:
            self.records.pop(memory_id, None)


class FakeOllamaResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"message": {"content": "Hello from AIrys"}, "eval_count": 12}


class FakeOllamaClient:
    requests = []

    def __init__(self, **_kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        pass

    async def post(self, url, json):
        self.requests.append({"url": url, "payload": json})
        return FakeOllamaResponse()


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.storage = FileStorage(str(root / "conversations"), str(root / "data"))
        self.vector_db = FakeVectorDatabase()
        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://test",
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        self.temp_dir.cleanup()

    async def test_memory_store_list_search_and_delete(self):
        with patch.object(memory_routes, "get_databases", return_value=(self.vector_db, self.storage)):
            created = await self.client.post(
                "/api/v1/memory/store",
                json={"content": "I prefer tea", "category": "preference"},
            )
            self.assertEqual(created.status_code, 200)
            memory_id = created.json()["data"][0]["id"]

            listed = await self.client.get("/api/v1/memory/list")
            self.assertEqual(listed.json()["data"][0]["text"], "I prefer tea")
            filtered = await self.client.get(
                "/api/v1/memory/list",
                params={"category": "preference"},
            )
            self.assertEqual(len(filtered.json()["data"]), 1)

            searched = await self.client.get(
                "/api/v1/memory/search",
                params={"query": "tea"},
            )
            self.assertEqual(searched.json()["data"][0]["id"], memory_id)

            legacy = await self.client.post(
                "/api/v1/memory/store",
                params={"memory_content": "Remember the old API", "category": "note"},
            )
            self.assertEqual(legacy.status_code, 200)

            deleted = await self.client.delete(f"/api/v1/memory/clear/{memory_id}")
            self.assertTrue(deleted.json()["success"])
            missing = await self.client.delete(f"/api/v1/memory/clear/{memory_id}")
            self.assertEqual(missing.status_code, 404)
            cleared = await self.client.delete("/api/v1/memory/clear-all")
            self.assertIn("1 memories", cleared.json()["message"])

    async def test_chat_uses_runtime_settings_and_persists_history(self):
        config = RuntimeConfig(
            ollama_host="http://localhost:11434",
            ollama_model="test-model",
            temperature=0.4,
            max_tokens=1024,
        )
        FakeOllamaClient.requests = []
        with (
            patch.object(chat_routes, "get_databases", return_value=(self.vector_db, self.storage)),
            patch.object(chat_routes, "get_runtime_config", return_value=config),
            patch.object(chat_routes.httpx, "AsyncClient", FakeOllamaClient),
        ):
            first = await self.client.post(
                "/api/v1/chat/complete",
                json={"message": "Remember that I like tea"},
            )
            second = await self.client.post(
                "/api/v1/chat/complete",
                json={"message": "What did I say?"},
            )
            self.assertEqual(first.status_code, 200)
            self.assertEqual(first.json()["tokens_used"], 12)
            self.assertEqual(second.status_code, 200)

            payload = FakeOllamaClient.requests[1]["payload"]
            self.assertEqual(payload["model"], "test-model")
            self.assertEqual(payload["options"]["temperature"], 0.4)
            self.assertIn(
                {"role": "user", "content": "Remember that I like tea"},
                payload["messages"],
            )
            history_response = await self.client.get("/api/v1/chat/history")
            self.assertEqual(len(history_response.json()["sessions"]), 2)

        history = self.storage.get_conversation("active_session")
        self.assertEqual(len(history["sessions"]), 2)

    async def test_settings_endpoints_return_and_apply_runtime_configuration(self):
        config = RuntimeConfig(
            ollama_host="http://localhost:11434",
            ollama_model="test-model",
            temperature=0.8,
            max_tokens=1024,
        )
        with (
            patch.object(settings_routes, "get_runtime_config", return_value=config),
            patch.object(settings_routes, "update_runtime_config", return_value=config) as update,
        ):
            current = await self.client.get("/api/v1/settings")
            self.assertEqual(current.json()["ollama_model"], "test-model")
            saved = await self.client.put("/api/v1/settings", json=config.model_dump())
            self.assertEqual(saved.json()["temperature"], 0.8)
            update.assert_called_once()


if __name__ == "__main__":
    unittest.main()
