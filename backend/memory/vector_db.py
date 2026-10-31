"""
ChromaDB Vector Database Wrapper
Provides semantic search and vector embedding capabilities
"""
import logging
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
            metadata={"category": {"dtype": "str"}, "created_at": {"dtype": "float"}}
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
        # Check for Ollama embedding API
        from config.app_config import settings
        ollama_host = settings.OLLAMA_HOST.replace("http://", "").replace("https://", "")
        
        try:
            import httpx
            ollama_port = ollama_host.split(":")[1] if ":" in ollama_host else "11434"
            
            # Try Ollama embedding API first (if available)
            response = httpx.get(
                f"http://{settings.OLLAMA_HOST}/api/embeddings",
                json={"model": settings.OLLAMA_MODEL, "prompt": text},
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                # Ollama returns {"embedding": [...]} by default
                embedding = result.get("embedding", [])
                
                # Normalize to -1 to 1 range (ChromaDB expects this)
                import numpy as np
                if embedding:
                    min_val = min(embedding)
                    max_val = max(embedding)
                    range_val = max_val - min_val
                    normalized = [(x - min_val) / range_val * 2 - 1 if range_val > 0 else 0 for x in embedding]
                    return list(normalized)
                return [0.0] * 768  # Default to zero vector if no embedding returned
                
        except Exception as e:
            logger.warning(f"Ollama embedding API not available: {e}. Falling back to sentence-transformers.")
        
        # Fallback to sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            
            model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight, fast model
            embedding = model.encode(text, convert_to_numpy=True)
            
            # Normalize the embedding vector (L2 normalization)
            import numpy as np
            embedding_normalized = embedding / np.linalg.norm(embedding)
            
            return embedding_normalized.tolist()
            
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            raise ValueError(f"Could not create embedding: {e}")
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        min_similarity: float = 0.5
    ) -> Optional[List[Dict[str, Any]]]:
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
            # Get vector for query
            query_embedding = self.create_embedding(query)
            
            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=min(n_results, 10)  # Cap at 10 for performance
            )
            
            # Filter by minimum similarity
            if not results or not results.get("distances") or not results.get("documents"):
                logger.warning(f"No results found for query '{query}'")
                return None
            
            distances = results["distances"][0]
            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            
            # Filter by similarity threshold
            filtered_indices = [
                i for i, dist in enumerate(distances) 
                if dist <= min_similarity  # Lower distance = higher similarity
            ]
            
            if not filtered_indices:
                logger.debug(f"No results above threshold {min_similarity} for query '{query}'")
                return None
            
            # Build result list
            memory_results = []
            for idx in sorted(filtered_indices):
                memory_results.append({
                    "text": documents[idx],
                    "score": 1.0 - distances[idx],  # Convert distance to similarity (0-1)
                    "metadata": metadatas[idx] or {},
                    "id": str(idx)  # Temporary ID, should use actual document ID in production
                })
            
            logger.info(f"Found {len(memory_results)} memories for query '{query}'")
            return memory_results
            
        except Exception as e:
            logger.error(f"Error searching memories: {e}")
            return None
    
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
        try:
            if metadatas is None:
                metadatas = [{"created_at": 0}] * len(ids)
            
            # Normalize embeddings to -1 to 1 range
            normalized_embeddings = []
            for emb in embeddings:
                import numpy as np
                emb_array = np.array(emb)
                norm = np.linalg.norm(emb_array)
                if norm > 0:
                    normalized_embeddings.append((emb_array / norm * 2 - 1).tolist())
                else:
                    normalized_embeddings.append([0.0] * len(emb))
            
            self.collection.upsert(
                ids=ids,
                embeddings=normalized_embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(ids)} memories to vector database")
            
        except Exception as e:
            # Use upsert for idempotency - won't fail if document already exists
            self.collection.upsert(
                ids=ids,
                embeddings=normalized_embeddings,
                documents=documents,
                metadatas=metadatas
            )
            logger.warning(f"Memory addition may have failed (using upsert): {e}")
    
    def delete(self, ids: List[str]):
        """
        Delete memories by their IDs.
        
        Args:
            ids: List of memory IDs to delete
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} memories from vector database")
        except Exception as e:
            logger.error(f"Error deleting memories: {e}")
