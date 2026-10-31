"""
AIrys Backend Server - FastAPI with Ollama integration
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
import uvicorn

logger = logging.getLogger(__name__)


# Import our components
from api.schemas import ChatRequest, MemoryResponse
from config.app_config import settings

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AIrys API",
    description="Personal AI Support Agent - Local LLM Interface",
    version=settings.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (for frontend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def startup():
    """Initialize connection to Ollama on startup."""
    logger.info(f"Starting AIrys server...")
    logger.info(f"Ollama host: {settings.OLLAMA_HOST}")


async def shutdown():
    """Cleanup on shutdown."""
    logger.info("Shutting down AIrys server...")


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "AIrys",
        "description": "Personal AI Support Agent - Local LLM Interface",
        "version": settings.API_VERSION,
        "docs": "/docs"
    }


# Include route modules (these will register their routes)
from api import chat_routes, memory_routes
app.include_router(chat_routes.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(memory_routes.router, prefix="/api/v1/memory", tags=["Memory"])


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG_MODE
    )
