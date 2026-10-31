"""
AIrys Backend Server - FastAPI with Ollama integration
"""
import sys
from pathlib import Path

# Add the backend and project root to the path for imports.
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn

logger = logging.getLogger(__name__)

# Import our components
from config.app_config import settings

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
from api import chat_routes, memory_routes, settings_routes
app.include_router(chat_routes.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(memory_routes.router, prefix="/api/v1/memory", tags=["Memory"])
app.include_router(settings_routes.router, prefix="/api/v1/settings", tags=["Settings"])


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG_MODE
    )
