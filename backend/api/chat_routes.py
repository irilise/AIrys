"""Chat and conversation history endpoints."""
import logging
import time
from functools import lru_cache

import httpx
from fastapi import APIRouter, HTTPException

from api.schemas import ChatRequest, ChatResponse
from config.app_config import get_runtime_config, settings
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


async def _installed_models(host: str) -> list[str]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{host}/api/tags")
            response.raise_for_status()
            return [m["name"] for m in response.json().get("models", [])]
    except Exception:
        return []


@router.post("/complete", response_model=ChatResponse)
async def complete_chat(request: ChatRequest):
    """Generate a reply grounded in recent conversation and relevant memories."""
    start_time = time.monotonic()
    vector_db, file_storage = get_databases()
    config = get_runtime_config()
    conversation = file_storage.get_conversation("active_session") or {"sessions": []}

    try:
        results = vector_db.search(
            query=request.message,
            n_results=3,
            min_similarity=0.65,
        )
        memory_context = "\n".join(result["text"] for result in results)
        context_parts = [part for part in (request.context, memory_context) if part]
        system_prompt = request.system_prompt or (
            "You are AIrys, a friendly and helpful personal assistant. "
            "Be conversational, practical, and supportive."
        )
        if context_parts:
            system_prompt += "\n\nRelevant context from the user's saved memories:\n" + "\n".join(context_parts)

        messages = [{"role": "system", "content": system_prompt}]
        for exchange in conversation["sessions"][-10:]:
            messages.extend([
                {"role": "user", "content": exchange["user_message"]},
                {"role": "assistant", "content": exchange["response"]},
            ])
        messages.append({"role": "user", "content": request.message})

        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{config.ollama_host}/api/chat",
                json={
                    "model": config.ollama_model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": config.temperature,
                        "num_predict": config.max_tokens,
                    },
                },
            )
        response.raise_for_status()
        result = response.json()
        ai_response = result.get("message", {}).get("content", "").strip()
        if not ai_response:
            raise HTTPException(status_code=502, detail="Ollama returned an empty response.")

        if request.persist_history:
            file_storage.save_conversation(
                key="active_session",
                message=request.message,
                response=ai_response,
                context="\n".join(context_parts) or None,
            )
        return ChatResponse(
            response=ai_response,
            tokens_used=result.get("eval_count"),
            latency_ms=(time.monotonic() - start_time) * 1000,
        )
    except HTTPException:
        raise
    except httpx.HTTPStatusError as error:
        logger.warning("Ollama returned an error: %s", error)
        if error.response.status_code == 404:
            installed = await _installed_models(config.ollama_host)
            detail = (
                f"Model '{config.ollama_model}' was not found on Ollama. "
                f"Pull it with 'ollama pull {config.ollama_model}' or choose an installed model in Settings"
                + (f" (installed: {', '.join(installed[:8])})." if installed else ".")
            )
        else:
            detail = f"Ollama returned HTTP {error.response.status_code}."
        raise HTTPException(status_code=502, detail=detail) from error
    except httpx.HTTPError as error:
        logger.warning("Ollama request failed: %s", error)
        raise HTTPException(
            status_code=503,
            detail=f"Could not reach Ollama at {config.ollama_host}. Check that it is running and the host is correct.",
        ) from error
    except Exception as error:
        logger.exception("Could not complete chat request")
        raise HTTPException(status_code=500, detail="Failed to complete chat request.") from error


@router.get("/history")
async def get_chat_history():
    """Return saved exchanges for the single local assistant session."""
    _, file_storage = get_databases()
    conversation = file_storage.get_conversation("active_session")
    return {"sessions": conversation["sessions"] if conversation else []}


@router.delete("/history")
async def clear_chat_history():
    """Clear the saved exchanges for the local assistant session."""
    _, file_storage = get_databases()
    file_storage.clear_conversation("active_session")
    return {"success": True, "message": "Conversation history cleared."}


@router.get("/health")
async def health_check():
    """Check that the API process is running."""
    return {"status": "healthy", "service": "AIrys"}
