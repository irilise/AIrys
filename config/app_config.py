"""
AIrys Configuration Management
Environment-based configuration with sensible defaults
"""
import os
import json
import logging
import threading
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    API_VERSION: str = "1.0.0"
    DEBUG_MODE: bool = False
    
    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 7860
    
    # Ollama Configuration
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    
    # Data Directories (relative to project root)
    DATA_DIR: str = "./data"
    CONVERSATIONS_DIR: str = "./data/conversations"
    EMBEDDINGS_DIR: str = "./data/embeddings"
    
    # Allowed CORS origins (frontend URLs)
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",  # Default React dev server
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite dev server
    ]
    
    # Model Configuration (optional overrides)
    EMBEDDING_MODEL: Optional[str] = None
    
    @property
    def allowed_origins_csv(self) -> str:
        """Get origins as comma-separated string."""
        return ", ".join(self.ALLOWED_ORIGINS)
    
    @property
    def embeddings_dir_full_path(self) -> str:
        """Get full path to embeddings directory."""
        return os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            self.EMBEDDINGS_DIR
        )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Cache settings for performance
@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()


class RuntimeConfig(BaseModel):
    """Ollama and inference settings that can be changed from the UI."""

    ollama_host: str = Field(min_length=1, max_length=2048)
    ollama_model: str = Field(min_length=1, max_length=128)
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=2048, ge=1, le=8192)

    @field_validator("ollama_host")
    @classmethod
    def validate_ollama_host(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        parsed = urlsplit(value)
        try:
            parsed.port
        except ValueError as error:
            raise ValueError("Ollama host must contain a valid port") from error
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Ollama host must be an HTTP(S) origin without credentials or a path")
        return value

    @field_validator("ollama_model")
    @classmethod
    def validate_ollama_model(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Ollama model cannot be empty")
        return value


_runtime_config: Optional[RuntimeConfig] = None
_runtime_config_lock = threading.RLock()


def _runtime_config_path() -> Path:
    return Path(settings.DATA_DIR).expanduser() / "settings.json"


def get_runtime_config() -> RuntimeConfig:
    """Load runtime settings once, using environment configuration as defaults."""
    global _runtime_config
    with _runtime_config_lock:
        if _runtime_config is not None:
            return _runtime_config.model_copy(deep=True)

        config_path = _runtime_config_path()
        if config_path.exists():
            try:
                saved = json.loads(config_path.read_text(encoding="utf-8"))
                # The host is only persisted when overridden, so each environment
                # (host vs. Docker) keeps using its own OLLAMA_HOST by default.
                saved.setdefault("ollama_host", settings.OLLAMA_HOST)
                _runtime_config = RuntimeConfig.model_validate(saved)
            except Exception as error:
                logger.exception("Could not load persisted runtime settings")
                raise RuntimeError(f"Invalid runtime settings in {config_path}") from error
        else:
            _runtime_config = RuntimeConfig(
                ollama_host=settings.OLLAMA_HOST,
                ollama_model=settings.OLLAMA_MODEL,
            )
        return _runtime_config.model_copy(deep=True)


def update_runtime_config(config: RuntimeConfig) -> RuntimeConfig:
    """Persist validated runtime settings and apply them to subsequent requests."""
    global _runtime_config
    with _runtime_config_lock:
        config_path = _runtime_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = config_path.with_suffix(".json.tmp")
        try:
            persisted = config.model_dump()
            if persisted["ollama_host"] == settings.OLLAMA_HOST.rstrip("/"):
                del persisted["ollama_host"]
            temporary_path.write_text(
                json.dumps(persisted, indent=2),
                encoding="utf-8",
            )
            os.replace(temporary_path, config_path)
        except OSError:
            logger.exception("Could not save runtime settings")
            if temporary_path.exists():
                temporary_path.unlink()
            raise

        _runtime_config = config.model_copy(deep=True)
        return _runtime_config.model_copy(deep=True)
