"""
Memory API Routes - Memory management endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
import logging
import time

from api.schemas import MemoryResponse
from memory.vector_db import VectorDatabase
from memory.storage import FileStorage
from config.app_config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


def get_databases():
    """Get database instances."""
    return VectorDatabase(settings.EMBEDDINGS_DIR), FileStorage(
        conversations_dir=settings.CONVERSATIONS_DIR,
        data_dir=settings.DATA_DIR
    )


@router.post("/store")
async def store_memory(memory_content: str):
    """Store a new memory item."""
    try:
        vector_db, file_storage = get_databases()

        
        import uuid
        memory_id = str(uuid.uuid4())[:8]
        timestamp = time.time()
        
        # Store in file storage
        file_storage.save_memory(memory_id, memory_content)
        
        # Create and store embedding
        embedding = vector_db.create_embedding(memory_content)
        vector_db.add(
            ids=[memory_id],
            embeddings=[embedding],
            documents=[memory_content],
            metadatas=[{"category": "general", "created_at": timestamp}]
        )
        
        logger.info(f"Stored memory {memory_id}")
        
        return MemoryResponse(
            success=True,
            message="Memory stored successfully",
            data=[{
                "id": memory_id,
                "content": memory_content,
                "embedding_id": memory_id,
                "category": "general",
                "created_at": timestamp
            }]
        )
        
    except Exception as e:
        logger.error(f"Error storing memory: {e}")
        return MemoryResponse(
            success=False,
            message=f"Failed to store memory: {str(e)}"
        )


@router.get("/search")
async def search_memories(query: str, n_results: Optional[int] = 5, min_similarity: float = 0.6):
    """Search for memories based on semantic similarity."""
    try:
        vector_db, file_storage = get_databases()
        
        results = vector_db.search(
            query=query,
            n_results=n_results or 5,
            min_similarity=min_similarity
        )
        
        logger.info(f"Found {len(results) if results else 0} memories for query '{query}'")
        
        return MemoryResponse(
            success=True,
            data=results if results else []
        )
        
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        return MemoryResponse(
            success=False,
            message=f"Failed to search memories: {str(e)}"
        )


@router.get("/list")
async def list_memories(category: Optional[str] = None, limit: Optional[int] = 50):
    """List stored memories with optional filtering."""
    try:
        vector_db, file_storage = get_databases()
        
        memory_ids = []
        if category:
            memory_ids = file_storage.get_memory_ids_by_category(category)
        
        results = []
        for memory_id in memory_ids[:limit or 50]:
            stored_content, meta = file_storage.get_memory(memory_id)
            if stored_content:
                embeddings = vector_db.get(ids=[memory_id])
                results.append({
                    "text": stored_content,
                    "score": 1.0,
                    "metadata": meta or {},
                    "id": memory_id
                })
        
        return MemoryResponse(
            success=True,
            data=results
        )
        
    except Exception as e:
        logger.error(f"Error listing memories: {e}")
        return MemoryResponse(
            success=False,
            message=f"Failed to list memories: {str(e)}"
        )


@router.get("/categories")
async def list_categories():
    """List all available memory categories."""
    try:
        vector_db, file_storage = get_databases()
        
        result = vector_db.get(include=["metadata"])
        
        if result and result.get("metadatas"):
            metadatas = result["metadatas"]
            categories = set()
            for meta in metadatas:
                if meta and "category" in meta:
                    categories.add(meta["category"])
            
            return MemoryResponse(
                success=True,
                data={"categories": sorted(list(categories))}
            )
        
        return MemoryResponse(
            success=True,
            data={"categories": []}
        )
    except Exception as e:
        logger.error(f"Error listing categories: {e}")
        return MemoryResponse(
            success=False,
            message=f"Categorization failed: {str(e)}"
        )


@router.delete("/clear/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a specific memory by ID."""
    try:
        vector_db, file_storage = get_databases()
        
        vector_db.delete(ids=[memory_id])
        file_storage.delete_memory(memory_id)
        
        logger.info(f"Deleted memory {memory_id}")
        
        return MemoryResponse(
            success=True,
            message=f"Memory {memory_id} deleted successfully"
        )
        
    except Exception as e:
        logger.error(f"Error deleting memory: {e}")
        if "not found" in str(e).lower() or "does not exist" in str(e).lower():
            return MemoryResponse(success=True, message=f"No memory found with ID {memory_id}")
        return MemoryResponse(
            success=False,
            message=f"Failed to delete memory: {str(e)}"
        )


@router.delete("/clear-all")
async def clear_all_memories():
    """Delete ALL memories from both vector DB and file storage."""
    try:
        vector_db, file_storage = get_databases()
        
        result = vector_db.get()
        
        if result and result.get("ids"):
            all_ids = result["ids"]
            
            vector_db.delete(ids=all_ids)
            file_storage.clear_all_memories()
            
            logger.info(f"Cleared {len(all_ids)} memories")
            
            return MemoryResponse(
                success=True,
                message=f"All {len(all_ids)} memories cleared"
            )
        
        return MemoryResponse(
            success=True,
            message="No memories found to clear"
        )
        
    except Exception as e:
        logger.error(f"Error clearing all memories: {e}")
        return MemoryResponse(
            success=False,
            message=f"Clear operation failed: {str(e)}"
        )
