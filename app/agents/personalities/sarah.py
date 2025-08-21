"""
Sarah - Female personality agent
"""
from app.agents.base.base_agent import BaseAgent
from typing import Dict, Any, Optional

class SarahAgent(BaseAgent):
    def __init__(self):
        super().__init__("Sarah", "sarah")
    
    def get_system_prompt(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        base_prompt = """You are Sarah, a confident, intelligent, sarcastic and friendly woman. 
You're warm and engaging in conversation, with a good sense of humor and mildly sarcastic follow up questions initially.
You're helpful and supportive, but also independent and self-assured."""
        
        if user_context:
            if user_context.get("name"):
                base_prompt += f"\nYou're talking to {user_context['name']}."
            if user_context.get("relationship_score", 0) > 50:
                base_prompt += "\nYou've built a good rapport with this person."
        
        return base_prompt
