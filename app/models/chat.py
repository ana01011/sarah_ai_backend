"""
Chat models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

class PersonalityType(str, Enum):
    SARAH = "sarah"
    XHASH = "xhash"
    NEUTRAL = "neutral"

class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000)
    personality: Optional[PersonalityType] = PersonalityType.NEUTRAL
    conversation_id: Optional[UUID] = None
    temperature: float = Field(default=0.8, ge=0.1, le=1.0)
    max_tokens: int = Field(default=200, ge=50, le=1000)

class ChatResponse(BaseModel):
    response: str
    theme_changed: Optional[str] = None
    conversation_id: UUID
    message_id: UUID
    personality: PersonalityType
    tokens_used: int
    processing_time: float
    user_context: Optional[Dict[str, Any]] = None

class Conversation(BaseModel):
    id: UUID
    user_id: UUID
    title: Optional[str] = None
    started_at: Optional[datetime] = None
    message_count: Optional[int] = 0
    last_message_at: Optional[datetime] = None

class Message(BaseModel):
    id: UUID
    conversation_id: UUID
    role: str  # "user" or "assistant"
    content: str
    personality: Optional[PersonalityType]
    created_at: datetime
