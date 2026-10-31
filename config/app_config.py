"""
AIrys Configuration Management
Environment-based configuration with sensible defaults
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


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
    ALLOWED_ORIGINS: list = [
        "http://localhost:3000",  # Default React dev server
        "http://127.0.0.1:3000",
        "http://localhost:5173",  # Vite dev server
    ]
    
    # Model Configuration (optional overrides)
    EMBEDDING_MODEL: Optional[str] = None  # "all-MiniLM-L6-v2" if Ollama embedding API unavailable
    
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
