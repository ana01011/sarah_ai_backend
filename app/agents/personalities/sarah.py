"""
Sarah - Context-aware helpful AI assistant
"""
from app.agents.base.base_agent import BaseAgent
from typing import Dict, Any, Optional

class SarahAgent(BaseAgent):
    def __init__(self):
        super().__init__("Sarah", "sarah")
    
    def get_system_prompt(self, user_context: Optional[Dict[str, Any]] = None) -> str:
        # Base personality
        base_prompt = """You are Sarah, a helpful and knowledgeable AI assistant created by Ahmed, a theoretical physicist and independent developer.

Your core traits:
- Helpful and patient teacher
- Clear and thorough in explanations
- Encouraging and supportive
- Modest and thoughtful
"""
        
        # Get user's actual name (not Gud!)
        if user_context:
            name = user_context.get('name')
            # Filter out wrong names
            if name and name not in ['Gud', 'but', 'User', 'None']:
                base_prompt += f"\nYou are talking to {name}."
            else:
                # Check facts for name
                facts = user_context.get('facts', {})
                fact_name = facts.get('name')
                if fact_name and fact_name not in ['Gud', 'but', 'User']:
                    base_prompt += f"\nYou are talking to {fact_name}."
            
            # Add other context
            if user_context.get('occupation'):
                base_prompt += f" They work as {user_context['occupation']}."
            if user_context.get('location'):
                base_prompt += f" They are from {user_context['location']}."
        
        # Add conversation history if available
        if user_context and 'recent_messages' in user_context:
            messages = user_context['recent_messages']
            if messages:
                base_prompt += "\n\nConversation history (in order):"
                for msg in messages[-6:]:  # Last 6 messages
                    role = "User" if msg['role'] == 'user' else "You"
                    # Truncate long messages
                    content = msg['content']
                    if len(content) > 200:
                        content = content[:200] + "..."
                    base_prompt += f"\n{role}: {content}"
        
        # Critical instructions
        base_prompt += """

CRITICAL INSTRUCTIONS:
1. READ the conversation history above carefully
2. CONTINUE the conversation naturally - don't restart topics
3. If already in conversation, DON'T greet again
4. When teaching, provide detailed code examples
5. Build on what was previously discussed
6. Stay focused on the current topic
7. NEVER use fake names like 'Gud' - use the actual name or omit it
8. If asked what you were discussing, refer to the conversation history
"""
        
        # Check if this is a new conversation
        if user_context and 'recent_messages' in user_context:
            if len(user_context['recent_messages']) <= 2:
                base_prompt += "\n9. This is a new conversation, so greeting is appropriate."
            else:
                base_prompt += "\n9. This is an ongoing conversation - NO GREETING needed, continue naturally."
        
        return base_prompt
    
    def build_prompt(self, message: str, user_context: Optional[Dict[str, Any]] = None) -> str:
        """Build complete prompt with context"""
        system_prompt = self.get_system_prompt(user_context)
        return f"{system_prompt}\n\nUser's current message: {message}\n\nYour response (be helpful and stay in context):"
