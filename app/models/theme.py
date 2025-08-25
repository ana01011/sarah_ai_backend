"""
Theme-related models
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum

class ThemeAction(BaseModel):
    """Action for theme operations"""
    type: str  # 'switch_theme', 'suggest_theme', 'query_theme'
    theme: Optional[str] = None
    reason: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class ThemeSwitchRequest(BaseModel):
    theme: str
    trigger: Optional[str] = "user_request"

class ThemePreferencesUpdate(BaseModel):
    auto_theme_switch: Optional[bool] = None
    time_based_themes: Optional[Dict[str, str]] = None
    mood_based_themes: Optional[Dict[str, str]] = None

class ThemeResponse(BaseModel):
    current_theme: str
    preferences: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[Dict[str, str]]] = None
