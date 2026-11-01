"""Memory management endpoints."""
import logging
import time
import uuid
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter, Body, HTTPException, Query

from api.schemas import MemoryCreate, MemoryResponse
from config.app_config import settings
from memory.storage import FileStorage
from memory.vector_db import VectorDatabase

logger = logging.getLogger(__name__)
router = APIRouter()


@lru_cache(maxsize=1)
def get_databases():
    return (
        VectorDatabase(settings.EMBEDDINGS_DIR),
        FileStorage(settings.CONVERSATIONS_DIR, settings.DATA_DIR),
    )


@router.post("/store", response_model=MemoryResponse)
async def store_memory(
    payload: Optional[MemoryCreate] = Body(default=None),
    memory_content: Optional[str] = Query(default=None, min_length=1, max_length=4096),
    category: str = Query(default="general", min_length=1, max_length=64),
):
    """Store a memory. JSON ``content`` is preferred; ``memory_content`` remains supported."""
    content = payload.content.strip() if payload else (memory_content or "").strip()
    memory_category = payload.category.strip() if payload else category.strip()
    if not content:
        raise HTTPException(status_code=422, detail="Memory content cannot be empty.")
    if not memory_category:
        raise HTTPException(status_code=422, detail="Memory category cannot be empty.")

    vector_db, file_storage = get_databases()
    memory_id = str(uuid.uuid4())
    created_at = time.time()
    try:
        embedding = vector_db.create_embedding(content)
        file_storage.save_memory(memory_id, content, memory_category, created_at)
        try:
            vector_db.add(
                ids=[memory_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[{"category": memory_category, "created_at": created_at}],
            )
        except Exception:
            file_storage.delete_memory(memory_id)
            raise

        return MemoryResponse(
            success=True,
            message="Memory stored successfully.",
            data=[{
                "id": memory_id,
                "content": content,
                "category": memory_category,
                "created_at": created_at,
            }],
        )
    except Exception as error:
        logger.exception("Could not store memory")
        raise HTTPException(status_code=500, detail="Failed to store memory.") from error


@router.get("/search", response_model=MemoryResponse)
async def search_memories(
    query: str = Query(min_length=1, max_length=4096),
    n_results: int = Query(default=5, ge=1, le=10),
    min_similarity: float = Query(default=0.6, ge=0, le=1),
):
    """Search saved memories by semantic similarity."""
    vector_db, _ = get_databases()
    try:
        results = vector_db.search(query=query, n_results=n_results, min_similarity=min_similarity)
        return MemoryResponse(success=True, data=results)
    except Exception as error:
        logger.exception("Could not search memories")
        raise HTTPException(status_code=500, detail="Failed to search memories.") from error


@router.get("/list", response_model=MemoryResponse)
async def list_memories(
    category: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    """List saved memories, optionally filtered by category."""
    _, file_storage = get_databases()
    try:
        memory_ids = (
            file_storage.get_memory_ids_by_category(category)
            if category
            else file_storage.get_all_memory_ids()
        )
        results = []
        for memory_id in memory_ids[:limit]:
            content, metadata = file_storage.get_memory(memory_id)
            if content is not None:
                results.append({
                    "id": memory_id,
                    "text": content,
                    "score": 1.0,
                    "metadata": metadata or {},
                })
        return MemoryResponse(success=True, data=results)
    except Exception as error:
        logger.exception("Could not list memories")
        raise HTTPException(status_code=500, detail="Failed to list memories.") from error


@router.get("/categories", response_model=MemoryResponse)
async def list_categories():
    """List categories currently used by saved memories."""
    _, file_storage = get_databases()
    try:
        return MemoryResponse(
            success=True,
            data={"categories": file_storage.get_memory_categories()},
        )
    except Exception as error:
        logger.exception("Could not list memory categories")
        raise HTTPException(status_code=500, detail="Failed to list memory categories.") from error


@router.delete("/clear/{memory_id}", response_model=MemoryResponse)
async def delete_memory(memory_id: str):
    """Delete a memory by ID."""
    vector_db, file_storage = get_databases()
    try:
        content, _ = file_storage.get_memory(memory_id)
        if content is None:
            raise HTTPException(status_code=404, detail="Memory not found.")
        vector_db.delete(ids=[memory_id])
        file_storage.delete_memory(memory_id)
        return MemoryResponse(success=True, message="Memory deleted.")
    except HTTPException:
        raise
    except Exception as error:
        logger.exception("Could not delete memory %s", memory_id)
        raise HTTPException(status_code=500, detail="Failed to delete memory.") from error


@router.delete("/clear-all", response_model=MemoryResponse)
async def clear_all_memories():
    """Delete all saved memories."""
    vector_db, file_storage = get_databases()
    try:
        memory_ids = file_storage.get_all_memory_ids()
        if memory_ids:
            vector_db.delete(ids=memory_ids)
        file_storage.clear_all_memories()
        return MemoryResponse(
            success=True,
            message=f"Cleared {len(memory_ids)} memories.",
        )
    except Exception as error:
        logger.exception("Could not clear memories")
        raise HTTPException(status_code=500, detail="Failed to clear memories.") from error
