"""Runtime model configuration endpoints."""
import logging

from fastapi import APIRouter, HTTPException

from config.app_config import RuntimeConfig, get_runtime_config, update_runtime_config

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=RuntimeConfig)
async def read_settings():
    """Return the active Ollama and inference settings."""
    try:
        return get_runtime_config()
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail="Could not load saved settings.") from error


@router.put("", response_model=RuntimeConfig)
async def save_settings(config: RuntimeConfig):
    """Persist validated settings for subsequent chat requests."""
    try:
        return update_runtime_config(config)
    except OSError as error:
        logger.exception("Could not save runtime settings")
        raise HTTPException(status_code=500, detail="Could not save settings.") from error
