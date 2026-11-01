"""
API Schemas for AIrys Backend
Defines request/response models using Pydantic
"""
from pydantic import BaseModel, Field
from typing import Any, List, Optional


class ChatRequest(BaseModel):
    """Request model for chat completion."""
    message: str = Field(..., min_length=1, max_length=4096, description="User's input message")
    context: Optional[str] = None  # Optional context from retrieved memories
    system_prompt: Optional[str] = Field(
        "You are AIrys, a friendly and helpful personal assistant. Be conversational, practical, and supportive.",
        description="System prompt to guide the AI's behavior"
    )
    persist_history: bool = Field(
        default=True,
        description="Whether to save this exchange to the local conversation history",
    )


class ChatResponse(BaseModel):
    """Response model for chat completion."""
    response: str = Field(..., description="AI's generated response")
    tokens_used: Optional[int] = Field(None, description="Number of tokens consumed")
    latency_ms: Optional[float] = Field(None, description="Request latency in milliseconds")


class MemoryItem(BaseModel):
    """Schema for stored memory item."""
    id: str = Field(..., description="Unique identifier for the memory")
    content: str = Field(..., description="The memory content")
    embedding_id: Optional[str] = Field(None, description="ID of vector embedding if stored")
    category: Optional[str] = Field(None, description="Memory category (e.g., 'task', 'preference', 'fact')")
    created_at: Optional[float] = Field(None, description="Timestamp in Unix format")


class MemoryResponse(BaseModel):
    """Response model for memory operations."""
    success: bool = Field(..., description="Whether operation succeeded")
    data: Optional[Any] = Field(None, description="Operation result, if applicable")
    message: Optional[str] = Field(None, description="Success or error message")


class MemoryCreate(BaseModel):
    """Request model for creating a memory."""
    content: str = Field(..., min_length=1, max_length=4096)
    category: str = Field(default="general", min_length=1, max_length=64)
