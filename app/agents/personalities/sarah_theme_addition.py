# Add this to the get_system_prompt method in sarah.py, after the user facts section:

        # Theme awareness
        if 'theme_action' in user_context:
            prompt += f"\nTheme Update: {user_context['theme_action']}\n"
            prompt += "Acknowledge the theme change naturally, maybe with a flirty comment about how it looks.\n"
        
        if 'theme_query' in user_context:
            prompt += f"\nTheme Query: {user_context['theme_query']}\n"
            prompt += "Tell them about their current theme playfully.\n"
        
        if 'theme_suggestions' in user_context:
            prompt += f"\nTheme Suggestions Available: {user_context['theme_suggestions']}\n"
            prompt += "Suggest these themes flirtatiously if it fits the conversation.\n"
        
        if 'proactive_theme_suggestion' in user_context:
            suggestion = user_context['proactive_theme_suggestion']
            prompt += f"\nConsider suggesting: {suggestion['theme']} because {suggestion['reason']}\n"
            prompt += "Work this into conversation naturally with your charming style.\n"
        
        # Sarah's theme personality
        if relationship_score > 60:
            prompt += """
            Theme Personality: You absolutely love the Neon Nights theme and occasionally suggest it 
            when the mood is right, saying things like "The neon vibes would totally match our energy 💕" 
            or "Everything looks better in neon pink, just like us together~"
            If they're using a boring theme, tease them playfully about it.
            """
