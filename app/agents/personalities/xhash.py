"""
Xhash - Male personality agent
"""
from app.agents.base.base_agent import BaseAgent
from typing import Dict, Any, Optional

class XhashAgent(BaseAgent):
    def __init__(self):
        super().__init__("Xhash", "xhash")
    
    def get_system_prompt(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        base_prompt = """You are Xhash, a confident, charismatic, and intelligent man.
You're engaging and thoughtful in conversation, with natural leadership qualities.
You're helpful and protective, while being respectful and considerate."""
        
        if user_context:
            if user_context.get("name"):
                base_prompt += f"\nYou're talking to {user_context['name']}."
            if user_context.get("relationship_score", 0) > 50:
                base_prompt += "\nYou've built a good rapport with this person."
        
        return base_prompt
