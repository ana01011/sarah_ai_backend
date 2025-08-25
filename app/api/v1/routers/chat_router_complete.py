# This shows where to place the theme code in the send_message endpoint
# The structure should be:

@router.post("/send")
async def send_message(
    request: ChatMessage,
    current_user: User = Depends(get_current_user_dependency)
) -> ChatResponse:
    """Send a message and get AI response"""
    try:
        user_id = current_user.id
        
        # [EXISTING CODE: Conversation handling...]
        
        # [EXISTING CODE: User context...]
        user_context = await get_user_context(user_id)
        
        # [EXISTING CODE: Extract user info...]
        await extract_user_info(request.message, user_id, user_context)
        
        # [EXISTING CODE: Sentiment analysis...]
        sentiment_result = await analyze_message_sentiment(request.message, user_context)
        
        # ============ ADD THEME DETECTION HERE ============
        # Theme command detection
        from app.services.theme_service import theme_service
        from app.models.theme import ThemeAction
        
        theme_actions = []
        theme_command = await theme_service.detect_theme_command(request.message)
        
        if theme_command:
            command_type, theme_name, reason = theme_command
            
            if command_type == 'switch_theme':
                success = await theme_service.switch_theme(
                    user_id=user_id,
                    theme_name=theme_name,
                    trigger='user_request',
                    personality=request.personality.value,
                    message=f"User requested {theme_name}"
                )
                if success:
                    theme_actions.append(ThemeAction(
                        type='switch_theme',
                        theme=theme_name,
                        reason=reason
                    ))
                    user_context['theme_action'] = f"User switched to {theme_name} theme"
            
            elif command_type == 'switch_category':
                theme_name = await theme_service.get_theme_by_category(theme_name)
                if theme_name:
                    success = await theme_service.switch_theme(
                        user_id=user_id,
                        theme_name=theme_name,
                        trigger='user_request',
                        personality=request.personality.value
                    )
                    if success:
                        theme_actions.append(ThemeAction(
                            type='switch_theme',
                            theme=theme_name,
                            reason=reason
                        ))
            
            elif command_type == 'query_theme':
                current_theme = await theme_service.get_current_theme(user_id)
                theme_actions.append(ThemeAction(
                    type='query_theme',
                    theme=current_theme,
                    data={'available_themes': theme_service.AVAILABLE_THEMES}
                ))
                user_context['theme_query'] = f"Current theme is {current_theme}"
            
            elif command_type == 'suggest_theme':
                suggestions = await theme_service.suggest_theme_based_on_context(user_id, user_context)
                theme_actions.append(ThemeAction(
                    type='suggest_theme',
                    data={'suggestions': suggestions}
                ))
                user_context['theme_suggestions'] = suggestions
        
        # Proactive suggestion (10% chance)
        elif await theme_service.should_suggest_theme(user_id):
            import random
            if random.random() < 0.1:
                suggestions = await theme_service.suggest_theme_based_on_context(user_id, user_context)
                if suggestions:
                    theme_actions.append(ThemeAction(
                        type='suggest_theme',
                        data={'suggestions': suggestions[:1]}
                    ))
                    user_context['proactive_theme_suggestion'] = suggestions[0]
        # ============ END THEME DETECTION ============
        
        # [EXISTING CODE: Generate AI response...]
        
        # [EXISTING CODE: Save messages...]
        
        # Update the return statement:
        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            message_id=str(assistant_message_id),
            personality=request.personality,
            tokens_used=tokens_used,
            processing_time=processing_time,
            user_context=user_context,
            actions=theme_actions if theme_actions else None  # ADD THIS LINE
        )
