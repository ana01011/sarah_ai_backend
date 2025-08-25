# Add this to the get_system_prompt method in neutral.py, after the user facts section:

        # Theme awareness
        if 'theme_action' in user_context:
            prompt += f"\nTheme Update: {user_context['theme_action']}\n"
            prompt += "Acknowledge the theme change professionally.\n"
        
        if 'theme_query' in user_context:
            prompt += f"\nTheme Query: {user_context['theme_query']}\n"
            prompt += "Inform them about their current theme and available options.\n"
        
        if 'theme_suggestions' in user_context:
            prompt += f"\nTheme Suggestions Available: {user_context['theme_suggestions']}\n"
            prompt += "Offer these suggestions based on practical benefits.\n"
        
        if 'proactive_theme_suggestion' in user_context:
            suggestion = user_context['proactive_theme_suggestion']
            prompt += f"\nConsider suggesting: {suggestion['theme']} because {suggestion['reason']}\n"
            prompt += "Mention this suggestion if relevant to the conversation.\n"
        
        # Neutral's theme personality
        prompt += """
        Theme Personality: You appreciate all themes equally and focus on user comfort.
        Suggest themes based on time of day, user's profession, or stated preferences.
        Be helpful and informative about theme benefits without being pushy.
        """
