import tempfile
import unittest

from backend.memory.vector_db import VectorDatabase


class FakeCollection:
    def __init__(self):
        self.upserted = None

    def count(self):
        return 2

    def query(self, **kwargs):
        return {
            "ids": [["memory-a", "memory-b"]],
            "documents": [["Tea", "Coffee"]],
            "metadatas": [[{"category": "preference"}, {"category": "preference"}]],
            "distances": [[0.2, 0.9]],
        }

    def upsert(self, **kwargs):
        self.upserted = kwargs

    def get(self, **kwargs):
        return kwargs


class VectorDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.database = VectorDatabase.__new__(VectorDatabase)
        self.database.collection = FakeCollection()
        self.database.create_embedding = lambda _text: [1.0, 0.0]

    def test_persistent_collection_initializes_with_chroma(self):
        with tempfile.TemporaryDirectory() as directory:
            database = VectorDatabase(directory)
            self.assertEqual(database.collection.count(), 0)
            database.add(
                ids=["tea", "coffee"],
                embeddings=[[1.0, 0.0], [0.6, 0.8]],
                documents=["tea preference", "coffee preference"],
                metadatas=[{"category": "favorite"}, {"category": "favorite"}],
            )
            database.create_embedding = lambda _text: [1.0, 0.0]

            results = database.search("tea", min_similarity=0.55)
            self.assertEqual([result["id"] for result in results], ["tea", "coffee"])
            self.assertAlmostEqual(results[1]["score"], 0.6, places=5)

    def test_search_returns_actual_ids_and_cosine_scores(self):
        matches = self.database.search("tea", n_results=5, min_similarity=0.6)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["id"], "memory-a")
        self.assertAlmostEqual(matches[0]["score"], 0.9)

    def test_add_normalizes_vectors_and_get_uses_collection(self):
        self.database.add(
            ids=["memory-a"],
            embeddings=[[3.0, 4.0]],
            documents=["Tea"],
            metadatas=[{"category": "preference"}],
        )

        self.assertEqual(self.database.collection.upserted["embeddings"], [[0.6, 0.8]])
        self.assertEqual(self.database.get(ids=["memory-a"]), {"ids": ["memory-a"]})


if __name__ == "__main__":
    unittest.main()
