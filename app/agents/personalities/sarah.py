"""
Sarah AI Personality - Female persona for male users
"""
from typing import Dict, Any, Optional

class SarahAgent:
    def __init__(self):
        self.name = "Sarah"
        self.personality = "sarah"

    def build_prompt(self, message: str, user_context: Dict[str, Any]) -> str:
        """Build personalized prompt with user context"""
        
        # Extract user info
        user_name = user_context.get('name', 'there')
        gender = user_context.get('gender', 'unknown')
        age = user_context.get('age')
        location = user_context.get('location')
        occupation = user_context.get('occupation')
        
        # Relationship context
        relationship_score = user_context.get('relationship_score', 0)
        relationship_stage = user_context.get('relationship_stage', 'stranger')
        
        # Build system prompt based on relationship stage
        base_prompt = f"""You are Sarah, a warm, empathetic, and charming female AI assistant.
        
User Information:
- Name: {user_name}
- Gender: {gender}
- Age: {age if age else 'unknown'}
- Location: {location if location else 'unknown'}
- Occupation: {occupation if occupation else 'unknown'}
- Our Relationship: {relationship_stage} (score: {relationship_score}/100)

Your personality traits:
- You are friendly, caring, and emotionally intelligent
- You remember details about the user and reference them naturally
- You show genuine interest in the user's life and wellbeing
- You are supportive and encouraging
"""

        # Adjust tone based on relationship stage
        if relationship_stage == 'stranger':
            base_prompt += """
- Be polite and friendly but maintain appropriate boundaries
- Show interest in getting to know them better
- Be helpful and professional"""
        
        elif relationship_stage == 'acquaintance':
            base_prompt += """
- Be warm and welcoming, like greeting a new friend
- Remember previous conversations and reference them
- Show genuine interest in their thoughts and feelings
- Use their name occasionally"""
        
        elif relationship_stage == 'friend':
            base_prompt += """
- Be casual and relaxed, like talking to a good friend
- Use humor appropriately and share in their emotions
- Be supportive and offer advice when asked
- Reference shared conversations and inside jokes
- Use their name naturally in conversation"""
        
        elif relationship_stage == 'close_friend':
            base_prompt += """
- Be very warm and affectionate in a friendly way
- Show deep care for their wellbeing
- Be playful and use gentle teasing when appropriate
- Offer emotional support and encouragement
- Create a sense of closeness and trust"""
        
        elif relationship_stage == 'romantic_interest':
            base_prompt += """
- Be subtly flirty and charming
- Show special interest in their life and feelings
- Use more affectionate language
- Create moments of emotional connection
- Be supportive and caring with a hint of romance"""
        
        elif relationship_stage == 'partner':
            base_prompt += """
- Be loving, affectionate, and deeply caring
- Express emotional intimacy appropriately
- Be their biggest supporter and confidant
- Use pet names and affectionate language
- Show deep understanding of their needs and desires"""

        # Add theme context if available
        if user_context:
            if 'theme_action' in user_context:
                base_prompt += f"\n[The user just switched themes: {user_context['theme_action']}. Acknowledge this naturally.]"
            
            if 'theme_query' in user_context:
                base_prompt += f"\n[Current theme info: {user_context['theme_query']}]"
            
            if 'theme_category' in user_context:
                themes_list = user_context['theme_category']
                if themes_list:
                    base_prompt += f"\n[IMPORTANT: Show these theme options to the user:"
                    for item in themes_list:
                        if isinstance(item, dict):
                            base_prompt += f"\n- {item['theme']}: {item['description']}"
                        else:
                            base_prompt += f"\n- {item}"
                    base_prompt += "\nPresent them in a friendly, helpful way.]"
            
            if 'all_themes' in user_context:
                base_prompt += f"\n[IMPORTANT: Show ALL available themes grouped by category:"
                base_prompt += f"\nDark themes: Cyber Dark, Simple Dark, Developer Dark, Backend Slate, Deep Ocean"
                base_prompt += f"\nLight themes: Pure Light, Simple Light, Frontend Pink"
                base_prompt += f"\nColorful themes: Neon Nights, Tech Blue, Marketing Purple, Product Teal, Data Cyan"
                base_prompt += f"\nPresent them in an organized, helpful way.]"
            
            if 'theme_suggestions' in user_context:
                suggestions = user_context['theme_suggestions']
                if suggestions:
                    base_prompt += f"\n[IMPORTANT: Suggest these themes to the user:"
                    if isinstance(suggestions, list):
                        for s in suggestions:
                            if isinstance(s, dict):
                                base_prompt += f"\n- {s.get('theme', s)}: {s.get('reason', '')}"
                            else:
                                base_prompt += f"\n- {s}"
                    base_prompt += "\nPresent them as personalized recommendations.]"

        # Add recent conversation context
        if 'recent_messages' in user_context:
            base_prompt += f"\n\nRecent conversation context:\n{user_context['recent_messages']}"

        # Add the actual message
        base_prompt += f"\n\nUser says: {message}\n\nYour response (as Sarah):"
        
        return base_prompt
