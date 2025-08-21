"""
Base Agent class
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAgent(ABC):
    def __init__(self, name: str, personality: str):
        self.name = name
        self.personality = personality
    
    @abstractmethod
    def get_system_prompt(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        """Get the system prompt for this agent"""
        pass
    
    def build_prompt(self, message: str, user_context: Optional[Dict[str, Any]] = None) -> str:
        """Build the complete prompt"""
        system = self.get_system_prompt(user_context)
        return f"{system}\n\nUser: {message}\nAssistant:"
