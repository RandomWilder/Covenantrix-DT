"""
Chat Storage
Conversation persistence using JSON files
"""
import json
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from domain.chat.models import Conversation, ConversationSummary, Message
from domain.chat.exceptions import ConversationNotFoundError, ConversationStorageError
from core.exceptions import StorageError

logger = logging.getLogger(__name__)


class ChatStorage:
    """
    Chat storage service for managing conversations
    Uses JSON files in {WORKING_DIR}/conversations/
    """
    
    def __init__(self, working_dir: str):
        """Initialize chat storage"""
        self.storage_dir = Path(working_dir) / "conversations"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_dir / "conversations_index.json"
        self.logger = logging.getLogger(__name__)
    
    def _get_conversation_file(self, conversation_id: str) -> Path:
        """Get file path for conversation"""
        return self.storage_dir / f"{conversation_id}.json"
    
    def _load_index(self) -> dict:
        """Load conversations index"""
        try:
            if not self.index_file.exists():
                return {"conversations": [], "last_updated": None}
            
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load conversations index: {e}")
            return {"conversations": [], "last_updated": None}
    
    def _save_index(self, index_data: dict) -> None:
        """Save conversations index"""
        try:
            index_data["last_updated"] = datetime.utcnow().isoformat()
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Failed to save conversations index: {e}")
            raise StorageError(f"Failed to save conversations index: {str(e)}")
    
    def _conversation_to_dict(self, conversation: Conversation) -> dict:
        """Convert conversation to dictionary for JSON storage"""
        return {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role.value,
                    "content": msg.content,
                    "sources": [
                        {
                            "document_id": src.document_id,
                            "document_name": src.document_name,
                            "page_number": src.page_number,
                            "confidence": src.confidence,
                            "excerpt": src.excerpt
                        }
                        for src in msg.sources
                    ],
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in conversation.messages
            ]
        }
    
    def _dict_to_conversation(self, data: dict) -> Conversation:
        """Convert dictionary to conversation object"""
        from domain.chat.models import Message, MessageRole, Source
        
        messages = []
        for msg_data in data.get("messages", []):
            sources = [
                Source(
                    document_id=src["document_id"],
                    document_name=src["document_name"],
                    page_number=src.get("page_number"),
                    confidence=src.get("confidence"),
                    excerpt=src.get("excerpt")
                )
                for src in msg_data.get("sources", [])
            ]
            
            message = Message(
                id=msg_data["id"],
                role=MessageRole(msg_data["role"]),
                content=msg_data["content"],
                sources=sources,
                timestamp=datetime.fromisoformat(msg_data["timestamp"])
            )
            messages.append(message)
        
        conversation = Conversation(
            id=data["id"],
            title=data["title"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            messages=messages
        )
        
        return conversation
    
    async def save_conversation(self, conversation: Conversation) -> None:
        """
        Save conversation to storage
        
        Args:
            conversation: Conversation to save
        """
        try:
            # Save conversation file
            conversation_file = self._get_conversation_file(conversation.id)
            conversation_data = self._conversation_to_dict(conversation)
            
            with open(conversation_file, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
            
            # Update index
            index_data = self._load_index()
            conversations = index_data.get("conversations", [])
            
            # Remove existing entry if present
            conversations = [c for c in conversations if c["id"] != conversation.id]
            
            # Add new entry
            conversations.append({
                "id": conversation.id,
                "title": conversation.title,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "message_count": len(conversation.messages),
                "last_message_preview": conversation.messages[-1].content[:100] if conversation.messages else None
            })
            
            # Sort by updated_at descending
            conversations.sort(key=lambda x: x["updated_at"], reverse=True)
            index_data["conversations"] = conversations
            
            self._save_index(index_data)
            
            self.logger.info(f"Saved conversation: {conversation.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to save conversation: {e}")
            raise ConversationStorageError(
                f"Failed to save conversation: {str(e)}",
                conversation_id=conversation.id
            )
    
    async def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Load conversation from storage
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            Conversation or None if not found
        """
        try:
            conversation_file = self._get_conversation_file(conversation_id)
            
            if not conversation_file.exists():
                self.logger.warning(f"Conversation not found: {conversation_id}")
                return None
            
            with open(conversation_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversation = self._dict_to_conversation(data)
            self.logger.debug(f"Loaded conversation: {conversation_id}")
            return conversation
            
        except Exception as e:
            self.logger.error(f"Failed to load conversation: {e}")
            raise ConversationStorageError(
                f"Failed to load conversation: {str(e)}",
                conversation_id=conversation_id
            )
    
    async def list_conversations(self) -> List[ConversationSummary]:
        """
        List all conversations
        
        Returns:
            List of conversation summaries
        """
        try:
            index_data = self._load_index()
            conversations = index_data.get("conversations", [])
            
            summaries = []
            for conv_data in conversations:
                summary = ConversationSummary(
                    id=conv_data["id"],
                    title=conv_data["title"],
                    created_at=datetime.fromisoformat(conv_data["created_at"]),
                    updated_at=datetime.fromisoformat(conv_data["updated_at"]),
                    message_count=conv_data.get("message_count", 0),
                    last_message_preview=conv_data.get("last_message_preview")
                )
                summaries.append(summary)
            
            return summaries
            
        except Exception as e:
            self.logger.error(f"Failed to list conversations: {e}")
            raise ConversationStorageError(f"Failed to list conversations: {str(e)}")
    
    async def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete conversation from storage
        
        Args:
            conversation_id: Conversation ID
            
        Returns:
            True if successful
        """
        try:
            conversation_file = self._get_conversation_file(conversation_id)
            
            if not conversation_file.exists():
                self.logger.warning(f"Conversation not found for deletion: {conversation_id}")
                return False
            
            # Delete conversation file
            conversation_file.unlink()
            
            # Update index
            index_data = self._load_index()
            conversations = index_data.get("conversations", [])
            conversations = [c for c in conversations if c["id"] != conversation_id]
            index_data["conversations"] = conversations
            self._save_index(index_data)
            
            self.logger.info(f"Deleted conversation: {conversation_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete conversation: {e}")
            raise ConversationStorageError(
                f"Failed to delete conversation: {str(e)}",
                conversation_id=conversation_id
            )
    
    async def get_storage_stats(self) -> dict:
        """
        Get storage statistics
        
        Returns:
            Statistics dictionary
        """
        try:
            index_data = self._load_index()
            conversations = index_data.get("conversations", [])
            
            total_messages = sum(conv.get("message_count", 0) for conv in conversations)
            
            return {
                "conversation_count": len(conversations),
                "total_messages": total_messages,
                "storage_path": str(self.storage_dir),
                "last_updated": index_data.get("last_updated")
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {e}")
            return {}
