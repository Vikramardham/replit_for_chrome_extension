"""
Chat-related data models.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Message roles in chat."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatMessage(BaseModel):
    """Represents a single chat message."""
    id: str = Field(..., description="Unique message ID")
    role: MessageRole = Field(..., description="Message role")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: str = Field(..., description="Session ID this message belongs to")


class ChatSession(BaseModel):
    """Represents a chat session."""
    id: str = Field(..., description="Unique session ID")
    user_id: Optional[str] = Field(None, description="User ID")
    title: str = Field(..., description="Session title")
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    extension_id: Optional[str] = Field(None, description="Associated extension ID") 