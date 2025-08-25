# Add this to your existing chat.py file
# The ChatResponse class should be updated to include actions:

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from app.models.theme import ThemeAction  # Add this import

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    message_id: str
    personality: PersonalityType
    tokens_used: int
    processing_time: float
    user_context: Optional[dict] = None
    actions: Optional[List[ThemeAction]] = None  # ADD THIS LINE
