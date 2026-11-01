"""
ChromaDB Vector Database Wrapper
Provides semantic search and vector embedding capabilities
"""
import logging
from functools import lru_cache
from typing import List, Optional, Dict, Any
import chromadb
import numpy as np

logger = logging.getLogger(__name__)


class VectorDatabase:
    """
    Wrapper around ChromaDB for semantic memory storage and retrieval.
    
    Features:
    - Semantic search using vector embeddings
    - Persistent file-based storage (no external database server needed)
    - Built-in collection management
    """
    
    def __init__(self, persist_directory: str):
        """
        Initialize ChromaDB client with persistence.
        
        Args:
            persist_directory: Path to directory for persistent storage
        """
        self.persist_directory = persist_directory
        
        # Create client with persistence
        self.client = chromadb.PersistentClient(
            path=persist_directory
        )
        
        # Create or get the memories collection
        # Metadata schema: {category, created_at}
        self.collection = self.client.get_or_create_collection(
            name="memories",
            metadata={"hnsw:space": "l2"},
        )
        
        logger.info(f"Vector database initialized at {persist_directory}")
    
    def create_embedding(self, text: str) -> List[float]:
        """
        Create a vector embedding for the given text.
        
        Uses Ollama's embedding API if configured, otherwise uses sentence-transformers.
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        from config.app_config import get_runtime_config, settings
        import httpx

        if settings.EMBEDDING_MODEL:
            try:
                config = get_runtime_config()
                response = httpx.post(
                    f"{config.ollama_host}/api/embed",
                    json={"model": settings.EMBEDDING_MODEL, "input": text},
                    timeout=30.0,
                )
                response.raise_for_status()
                result = response.json()
                embeddings = result.get("embeddings")
                embedding = embeddings[0] if embeddings else result.get("embedding")
                if embedding:
                    return self._normalize_embedding(embedding)
                logger.warning("Ollama returned an empty embedding; trying sentence-transformers")
            except (httpx.HTTPError, ValueError) as error:
                logger.warning("Ollama embeddings unavailable: %s", error)

        # Fallback to sentence-transformers
        try:
            model = self._get_fallback_model()
            embedding = model.encode(text, convert_to_numpy=True)

            return self._normalize_embedding(embedding.tolist())
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            raise ValueError(f"Could not create embedding: {e}")

    @staticmethod
    @lru_cache(maxsize=1)
    def _get_fallback_model():
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer("all-MiniLM-L6-v2")

    @staticmethod
    def _normalize_embedding(embedding: List[float]) -> List[float]:
        values = np.asarray(embedding, dtype=float)
        norm = np.linalg.norm(values)
        if not np.isfinite(norm) or norm == 0:
            raise ValueError("Embedding must contain finite, non-zero values")
        return (values / norm).tolist()
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for memories similar to the query using semantic similarity.
        
        Args:
            query: The search query
            n_results: Number of results to return
            min_similarity: Minimum cosine similarity threshold
            
        Returns:
            List of matching memories with similarity scores, or None if no matches
        """
        try:
            if self.collection.count() == 0:
                return []
            # Get vector for query
            query_embedding = self.create_embedding(query)
            
            if n_results < 1:
                raise ValueError("n_results must be greater than zero")

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, 10),
            )
            if not results or not results.get("ids") or not results["ids"][0]:
                return []

            distances = results["distances"][0]
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            ids = results["ids"][0]
            memory_results = []
            for memory_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
                # Chroma's L2 distance is squared; for unit vectors it equals 2 - 2*cosine.
                score = max(0.0, min(1.0, 1.0 - distance / 2))
                if score >= min_similarity:
                    memory_results.append({
                        "text": document,
                        "score": score,
                        "metadata": metadata or {},
                        "id": memory_id,
                    })

            logger.info("Found %s memories for query", len(memory_results))
            return memory_results
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            raise
    
    def add(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Add new memories to the vector database.
        
        Args:
            ids: Unique identifiers for each memory
            embeddings: Vector embeddings for each document
            documents: The actual text content
            metadatas: Optional metadata (category, timestamp, etc.)
        """
        if not (len(ids) == len(embeddings) == len(documents)):
            raise ValueError("ids, embeddings, and documents must have equal lengths")
        if metadatas is None:
            metadatas = [{"created_at": 0}] * len(ids)
        if len(metadatas) != len(ids):
            raise ValueError("metadatas must match the number of ids")

        self.collection.upsert(
            ids=ids,
            embeddings=[self._normalize_embedding(embedding) for embedding in embeddings],
            documents=documents,
            metadatas=metadatas,
        )
        logger.info("Added %s memories to vector database", len(ids))

    def get(self, ids: Optional[List[str]] = None, include: Optional[List[str]] = None):
        """Return memory records, optionally restricted to their IDs."""
        options = {"include": include} if include is not None else {}
        if ids is not None:
            options["ids"] = ids
        return self.collection.get(**options)
    
    def delete(self, ids: List[str]):
        """
        Delete memories by their IDs.
        
        Args:
            ids: List of memory IDs to delete
        """
        self.collection.delete(ids=ids)
        logger.info("Deleted %s memories from vector database", len(ids))
