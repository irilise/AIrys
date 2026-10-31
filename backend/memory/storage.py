"""
File-based Storage Manager for AIrys
Handles persistent storage of conversations and memories using JSON files
"""
import os
import json
import logging
import time
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class FileStorage:
    """
    File-based storage system for AIrys.
    
    Stores conversation histories and memory metadata/content in JSON files.
    ChromaDB stores the memory vectors separately.
    """
    
    def __init__(self, conversations_dir: str, data_dir: str):
        """
        Initialize file storage system.
        
        Args:
            conversations_dir: Directory for conversation storage
            data_dir: Root data directory
        """
        self.data_root = Path(data_dir)
        self.conversations_dir = Path(conversations_dir)
        
        # Create directories if they don't exist
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        
        # Memory metadata storage (lightweight JSON tracking)
        self._ensure_memories_metadata()
        
        logger.info(f"File storage initialized at {self.conversations_dir}")
    
    def _ensure_memories_metadata(self):
        """Create memories metadata file if it doesn't exist."""
        metadata_file = self.conversations_dir / "memories_metadata.json"
        if not metadata_file.exists():
            self._write_json(metadata_file, {"memories": {}})

    @staticmethod
    def _write_json(path: Path, data: Dict[str, Any]):
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    
    def save_conversation(self, key: str, message: str, response: str, 
                         context: Optional[str] = None):
        """
        Save a conversation exchange to file storage.
        
        Args:
            key: Conversation session identifier
            message: User's message
            response: AI's response
            context: Retrieved memory context (if any)
        """
        try:
            # Get or create conversation file
            conv_file = self.conversations_dir / f"{key}.json"

            if not conv_file.exists():
                data = {
                    "sessions": []
                }
            else:
                data = json.loads(conv_file.read_text(encoding="utf-8"))
            
            # Create session entry
            timestamp = datetime.now().isoformat()
            
            if context:
                session_entry = {
                    "type": "contextual",
                    "timestamp": timestamp,
                    "user_message": message,
                    "response": response,
                    "retrieved_context": context
                }
            else:
                session_entry = {
                    "type": "general",
                    "timestamp": timestamp,
                    "user_message": message,
                    "response": response
                }
            
            data["sessions"].append(session_entry)
            self._write_json(conv_file, data)
            
            logger.debug(f"Saved conversation {key}: '{message[:50]}...'")
            
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            raise
    
    def get_conversation(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve all conversations for a given session key.
        
        Args:
            key: Conversation session identifier
            
        Returns:
            Dictionary with sessions list, or None if not found
        """
        try:
            conv_file = self.conversations_dir / f"{key}.json"
            
            if not conv_file.exists():
                return None
            
            data = json.loads(conv_file.read_text(encoding="utf-8"))
            return {"sessions": data.get("sessions", [])}

        except Exception as e:
            logger.error(f"Error loading conversation {key}: {e}")
            raise

    def clear_conversation(self, key: str):
        """Remove the saved exchanges for a conversation."""
        conversation_file = self.conversations_dir / f"{key}.json"
        if conversation_file.exists():
            conversation_file.unlink()

    def save_memory(
        self,
        memory_id: str,
        content: str,
        category: Optional[str] = None,
        created_at: Optional[float] = None,
    ):
        """
        Save the local content and metadata record for a memory.
        
        Args:
            memory_id: The unique identifier for the memory
            content: The stored content
            category: Memory category
        """
        try:
            self._ensure_memories_metadata()
            
            # Load existing metadata
            metadata_file = self.conversations_dir / "memories_metadata.json"
            data = json.loads(metadata_file.read_text(encoding="utf-8"))
            
            # Add or update memory tracking
            data["memories"][memory_id] = {
                "content": content,
                "category": category,
                "created_at": created_at if created_at is not None else time.time(),
            }
            
            self._write_json(metadata_file, data)
            
        except Exception as e:
            logger.error(f"Error saving memory metadata: {e}")
            raise
    
    def update_memory(self, memory_id: str, updates: Dict[str, Any]):
        """
        Update an existing memory's metadata.
        
        Args:
            memory_id: The memory ID to update
            updates: Dictionary of fields to update
        """
        try:
            self._ensure_memories_metadata()
            
            metadata_file = self.conversations_dir / "memories_metadata.json"
            data = json.loads(metadata_file.read_text(encoding="utf-8"))
            
            if memory_id in data["memories"]:
                data["memories"][memory_id].update(updates)
                self._write_json(metadata_file, data)
            
        except Exception as e:
            logger.error(f"Error updating memory: {e}")
            raise
    
    def get_memory(self, memory_id: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Retrieve a memory by ID.
        
        Args:
            memory_id: The memory identifier
            
        Returns:
            Tuple of (content, metadata) or (None, None) if not found
        """
        try:
            self._ensure_memories_metadata()
            
            metadata_file = self.conversations_dir / "memories_metadata.json"
            data = json.loads(metadata_file.read_text())
            
            if memory_id in data["memories"]:
                content = data["memories"][memory_id]["content"]
                meta = {k: v for k, v in data["memories"][memory_id].items() 
                       if k not in ["content"]}
                return (content, meta)
            
            return (None, None)
        
        except Exception as e:
            logger.error(f"Error getting memory {memory_id}: {e}")
            raise
    
    def get_memory_ids_by_category(self, category: str) -> list:
        """
        Get all memory IDs filtered by category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of memory IDs matching the category
        """
        try:
            self._ensure_memories_metadata()
            
            metadata_file = self.conversations_dir / "memories_metadata.json"
            data = json.loads(metadata_file.read_text(encoding="utf-8"))
            
            return [
                mem_id for mem_id, meta in data["memories"].items()
                if meta and "category" in meta and meta["category"] == category
            ]
        
        except Exception as e:
            logger.error(f"Error getting memory IDs by category: {e}")
            raise

    def get_all_memory_ids(self) -> list:
        """Return all memory IDs in insertion order."""
        try:
            self._ensure_memories_metadata()
            metadata_file = self.conversations_dir / "memories_metadata.json"
            data = json.loads(metadata_file.read_text(encoding="utf-8"))
            return list(data["memories"])
        except Exception as e:
            logger.error(f"Error getting all memory IDs: {e}")
            raise

    def get_memory_categories(self) -> list:
        """Return unique memory categories in alphabetical order."""
        try:
            self._ensure_memories_metadata()
            metadata_file = self.conversations_dir / "memories_metadata.json"
            data = json.loads(metadata_file.read_text(encoding="utf-8"))
            return sorted({
                metadata["category"]
                for metadata in data["memories"].values()
                if metadata.get("category")
            })
        except Exception as e:
            logger.error(f"Error getting memory categories: {e}")
            raise
    
    def clear_all_memories(self):
        """
        Clear all memories from storage.
        
        This is a destructive operation - removes ALL tracked memories.
        """
        try:
            self._ensure_memories_metadata()
            
            metadata_file = self.conversations_dir / "memories_metadata.json"
            data = json.loads(metadata_file.read_text(encoding="utf-8"))
            
            # Clear all memory IDs
            data["memories"] = {}
            self._write_json(metadata_file, data)
        
        except Exception as e:
            logger.error(f"Error clearing all memories: {e}")
            raise
    
    def delete_memory(self, memory_id: str):
        """
        Delete a memory and its metadata.
        
        Args:
            memory_id: The memory ID to delete
        """
        try:
            # Delete metadata
            self._ensure_memories_metadata()
            
            metadata_file = self.conversations_dir / "memories_metadata.json"
            data = json.loads(metadata_file.read_text(encoding="utf-8"))
            
            if memory_id in data["memories"]:
                del data["memories"][memory_id]
                self._write_json(metadata_file, data)
                
        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {e}")
            raise
    
    def get_all_conversations(self) -> Dict[str, Any]:
        """
        Get all available conversation keys.
        
        Returns:
            Dictionary mapping conversation keys to their data
        """
        try:
            conversations = {}
            
            for conv_file in self.conversations_dir.glob("*.json"):
                if conv_file.name != "memories_metadata.json":
                    data = json.loads(conv_file.read_text(encoding="utf-8"))
                    key = conv_file.stem
                    conversations[key] = data
            
            return conversations
            
        except Exception as e:
            logger.error(f"Error loading all conversations: {e}")
            raise
