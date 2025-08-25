"""
Theme API Router
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from app.models.auth import User
from app.models.theme import ThemeSwitchRequest, ThemePreferencesUpdate, ThemeResponse
from app.api.v1.routers.auth_router import get_current_user_dependency
from app.services.theme_service import theme_service
from app.core.database import db
import json

router = APIRouter(prefix="/themes", tags=["themes"])

@router.get("/current", response_model=ThemeResponse)
async def get_current_theme(
    current_user: User = Depends(get_current_user_dependency)
) -> ThemeResponse:
    """Get user's current theme and preferences"""
    current_theme = await theme_service.get_current_theme(current_user.id)
    preferences = await theme_service.get_user_preferences(current_user.id)
    
    return ThemeResponse(
        current_theme=current_theme,
        preferences=preferences
    )

@router.post("/switch")
async def switch_theme(
    request: ThemeSwitchRequest,
    current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Switch to a different theme"""
    if request.theme not in theme_service.AVAILABLE_THEMES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid theme. Available themes: {', '.join(theme_service.AVAILABLE_THEMES)}"
        )
    
    success = await theme_service.switch_theme(
        user_id=current_user.id,
        theme_name=request.theme,
        trigger=request.trigger
    )
    
    if success:
        return {
            "success": True,
            "message": f"Theme switched to {request.theme}",
            "theme": request.theme
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to switch theme")

@router.get("/available")
async def get_available_themes(
    current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Get all available themes"""
    themes = await db.fetch("""
        SELECT * FROM available_themes ORDER BY category, theme_name
    """)
    
    return {
        "themes": theme_service.AVAILABLE_THEMES,
        "details": [dict(theme) for theme in themes] if themes else []
    }

@router.get("/suggestions")
async def get_theme_suggestions(
    current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Get AI theme suggestions"""
    # Get user context
    from app.api.v1.routers.chat_router import get_user_context
    context = await get_user_context(current_user.id)
    
    suggestions = await theme_service.suggest_theme_based_on_context(
        current_user.id, 
        context
    )
    
    return {
        "current_theme": await theme_service.get_current_theme(current_user.id),
        "suggestions": suggestions
    }

@router.put("/preferences")
async def update_preferences(
    preferences: ThemePreferencesUpdate,
    current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, str]:
    """Update theme preferences"""
    updates = []
    params = [current_user.id]
    param_count = 1
    
    if preferences.auto_theme_switch is not None:
        param_count += 1
        updates.append(f"auto_theme_switch = ${param_count}")
        params.append(preferences.auto_theme_switch)
    
    if preferences.time_based_themes:
        param_count += 1
        updates.append(f"time_based_themes = ${param_count}::jsonb")
        params.append(json.dumps(preferences.time_based_themes))
    
    if preferences.mood_based_themes:
        param_count += 1
        updates.append(f"mood_based_themes = ${param_count}::jsonb")
        params.append(json.dumps(preferences.mood_based_themes))
    
    if updates:
        query = f"""
            UPDATE user_preferences 
            SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $1
        """
        await db.execute(query, *params)
    
    return {"message": "Preferences updated successfully"}

@router.get("/history")
async def get_theme_history(
    current_user: User = Depends(get_current_user_dependency)
) -> Dict[str, Any]:
    """Get user's theme change history"""
    prefs = await theme_service.get_user_preferences(current_user.id)
    history = json.loads(prefs.get('theme_history', '[]')) if prefs.get('theme_history') else []
    
    interactions = await db.fetch("""
        SELECT theme_name, action, trigger, ai_personality, timestamp
        FROM theme_interactions
        WHERE user_id = $1
        ORDER BY timestamp DESC
        LIMIT 20
    """, current_user.id)
    
    return {
        "current_theme": prefs.get('preferred_theme', 'Cyber Dark'),
        "change_count": prefs.get('theme_change_count', 0),
        "history": history,
        "interactions": [dict(i) for i in interactions] if interactions else []
    }
