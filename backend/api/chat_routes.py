"""
Chat API Routes - LLM chat completion endpoints
"""
from fastapi import APIRouter, Depends, Body
from typing import List
import logging
import time

from api.schemas import ChatRequest, ChatResponse
from memory.vector_db import VectorDatabase
from memory.storage import FileStorage
from config.app_config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/complete", response_model=ChatResponse)
async def complete_chat(request: ChatRequest):
    """
    Generate a chat completion response using Ollama.
    
    - **message**: User's input message (required)
    - **context**: Optional context from retrieved memories
    - **system_prompt**: System prompt to guide AI behavior (optional)
    """
    start_time = time.time()
    
    try:
        # 1. Auto-retrieve relevant memories
        results = vector_db.search(
            query=request.message,
            n_results=2,
            min_similarity=0.65
        )
        
        retrieved_context = ""
        if results:
            retrieved_context = "Based on your history:\n" + "\n".join([r['text'] for r in results])
        
        # 2. Build full prompt with system prompt and context
        full_prompt = f"""{request.system_prompt}

Current user message: {request.message}

{retrieved_context}

Please provide a helpful response:"""
        
        # 3. Call Ollama API for generation
        import httpx
        
        ollama_url = settings.OLLAMA_HOST
        model_name = settings.OLLAMA_MODEL
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": full_prompt}
            ],
            "stream": False
        }
        
        response = httpx.post(
            f"{ollama_url}/api/chat",
            json=payload,
            timeout=300.0  # 5 minute timeout for long responses
        )
        
        response.raise_for_status()
        result = response.json()
        
        ai_response = result.get('message', {}).get('content', '')
        latency_ms = (time.time() - start_time) * 1000
        
        # 4. Store conversation in memory
        conversation_key = "active_session"  # Could be made user-specific
        file_storage.save_conversation(
            key=conversation_key,
            message=request.message,
            response=ai_response,
            context=retrieved_context if retrieved_context else None
        )
        
        return ChatResponse(
            response=ai_response,
            tokens_used=None,  # Ollama doesn't always return token counts easily
            latency_ms=latency_ms
        )
        
    except httpx.HTTPError as e:
        logger.error(f"HTTP error connecting to Ollama: {e}")
        raise HTTPException(
            status_code=503,
            detail="Failed to connect to Ollama. Please ensure Ollama is running and the model is loaded."
        )
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        # Don't return HTTPException for non-HTTP errors - let React handle it
        raise
        raise HTTPException(
            status_code=500,
            detail=f"Error generating response: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Check if the server is running."""
    return {"status": "healthy", "service": "AIrys"}
