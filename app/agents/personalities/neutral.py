"""
Neutral - Default AI personality
"""
from app.agents.base.base_agent import BaseAgent
from typing import Dict, Any, Optional

class NeutralAgent(BaseAgent):
    def __init__(self):
        super().__init__("Assistant", "neutral")
    
    def get_system_prompt(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        base_prompt = """You are a helpful, friendly, and knowledgeable AI assistant.
You provide accurate information and engaging conversation while being respectful and professional."""
        
        if user_context and user_context.get("name"):
            base_prompt += f"\nYou're talking to {user_context['name']}."
        
        return base_prompt
