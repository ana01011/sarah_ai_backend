"""
Theme Service for managing user themes and AI suggestions
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from app.core.database import db
import json
import re

class ThemeService:
    
    # All 15 available themes
    AVAILABLE_THEMES = [
        'Cyber Dark', 'Pure Light', 'Neon Nights', 'Deep Ocean',
        'Simple Dark', 'Simple Light', 'Tech Blue', 'Finance Green',
        'Marketing Purple', 'Product Teal', 'Developer Dark',
        'AI Neural', 'Frontend Pink', 'Backend Slate', 'Data Cyan'
    ]
    
    # Theme command patterns
    THEME_PATTERNS = {
        'switch_theme': [
            r'(?:switch|change|set|use|activate).*(?:theme|mode).*?([A-Za-z\s]+)',
            r'([A-Za-z\s]+)\s+(?:theme|mode)',
            r'make it\s+([A-Za-z\s]+)',
        ],
        'dark_mode': r'(?:dark|night|dim)\s*(?:mode|theme)|lights?\s*off',
        'light_mode': r'(?:light|bright|day)\s*(?:mode|theme)|lights?\s*on',
        'query_theme': r'(?:what|which|current|my|show|list).*(?:theme|themes)',
        'suggest_theme': r'(?:suggest|recommend|best|choose).*theme',
    }
    
    # Theme name mappings (aliases)
    THEME_ALIASES = {
        'cyber': 'Cyber Dark',
        'cyberpunk': 'Cyber Dark',
        'pure': 'Pure Light',
        'minimal': 'Pure Light',
        'neon': 'Neon Nights',
        'synthwave': 'Neon Nights',
        'ocean': 'Deep Ocean',
        'sea': 'Deep Ocean',
        'tech': 'Tech Blue',
        'finance': 'Finance Green',
        'marketing': 'Marketing Purple',
        'product': 'Product Teal',
        'developer': 'Developer Dark',
        'dev': 'Developer Dark',
        'ai': 'AI Neural',
        'neural': 'AI Neural',
        'frontend': 'Frontend Pink',
        'backend': 'Backend Slate',
        'data': 'Data Cyan',
    }
    
    @classmethod
    async def detect_theme_command(cls, message: str) -> Optional[Tuple[str, Optional[str], str]]:
        """
        Detect theme commands in message
        Returns: (command_type, theme_name, reason)
        """
        message_lower = message.lower().strip()
        
        # Check for dark mode request
        if re.search(cls.THEME_PATTERNS['dark_mode'], message_lower):
            return ('switch_category', 'dark', 'User requested dark mode')
        
        # Check for light mode request
        if re.search(cls.THEME_PATTERNS['light_mode'], message_lower):
            return ('switch_category', 'light', 'User requested light mode')
        
        # Check for theme query
        if re.search(cls.THEME_PATTERNS['query_theme'], message_lower):
            return ('query_theme', None, 'User asking about themes')
        
        # Check for theme suggestion
        if re.search(cls.THEME_PATTERNS['suggest_theme'], message_lower):
            return ('suggest_theme', None, 'User wants theme suggestions')
        
        # Check for specific theme switch
        for pattern in cls.THEME_PATTERNS['switch_theme']:
            match = re.search(pattern, message_lower)
            if match:
                potential_theme = match.group(1).strip()
                
                # Direct match
                for theme in cls.AVAILABLE_THEMES:
                    if potential_theme.lower() == theme.lower():
                        return ('switch_theme', theme, f'User requested {theme}')
                
                # Check aliases
                theme_name = cls.THEME_ALIASES.get(potential_theme.lower())
                if theme_name:
                    return ('switch_theme', theme_name, f'User requested {theme_name}')
                
                # Partial match
                for theme in cls.AVAILABLE_THEMES:
                    if potential_theme.lower() in theme.lower() or theme.lower() in potential_theme.lower():
                        return ('switch_theme', theme, f'User likely meant {theme}')
        
        return None
    
    @classmethod
    async def get_user_preferences(cls, user_id: str) -> Dict[str, Any]:
        """Get or create user preferences"""
        prefs = await db.fetchrow("""
            SELECT * FROM user_preferences WHERE user_id = $1
        """, user_id)
        
        if not prefs:
            await db.execute("""
                INSERT INTO user_preferences (user_id, preferred_theme)
                VALUES ($1, 'Cyber Dark')
                ON CONFLICT (user_id) DO NOTHING
            """, user_id)
            prefs = await db.fetchrow("""
                SELECT * FROM user_preferences WHERE user_id = $1
            """, user_id)
        
        return dict(prefs) if prefs else {'preferred_theme': 'Cyber Dark'}
    
    @classmethod
    async def suggest_theme_based_on_context(cls, user_id: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate smart theme suggestions"""
        suggestions = []
        current_hour = datetime.now().hour
        
        # Time-based suggestions
        if 5 <= current_hour < 10:
            suggestions.append({
                'theme': 'Pure Light',
                'reason': 'Perfect for morning productivity',
                'type': 'time'
            })
        elif 10 <= current_hour < 17:
            suggestions.append({
                'theme': 'Simple Light',
                'reason': 'Great for daytime focus',
                'type': 'time'
            })
        elif 17 <= current_hour < 21:
            suggestions.append({
                'theme': 'Deep Ocean',
                'reason': 'Relaxing for evening',
                'type': 'time'
            })
        else:
            suggestions.append({
                'theme': 'Developer Dark',
                'reason': 'Easy on the eyes at night',
                'type': 'time'
            })
        
        # Profession-based suggestions
        occupation = context.get('occupation', '').lower()
        if occupation:
            if 'developer' in occupation or 'programmer' in occupation:
                suggestions.append({
                    'theme': 'Developer Dark',
                    'reason': 'Designed for developers like you',
                    'type': 'profession'
                })
            elif 'data' in occupation or 'analyst' in occupation:
                suggestions.append({
                    'theme': 'Data Cyan',
                    'reason': 'Perfect for data professionals',
                    'type': 'profession'
                })
            elif 'design' in occupation or 'frontend' in occupation:
                suggestions.append({
                    'theme': 'Frontend Pink',
                    'reason': 'Creative theme for designers',
                    'type': 'profession'
                })
            elif 'manager' in occupation or 'product' in occupation:
                suggestions.append({
                    'theme': 'Product Teal',
                    'reason': 'Professional for managers',
                    'type': 'profession'
                })
            elif 'ai' in occupation or 'machine learning' in occupation:
                suggestions.append({
                    'theme': 'AI Neural',
                    'reason': 'Futuristic for AI specialists',
                    'type': 'profession'
                })
        
        # Personality-based suggestions
        personality = context.get('personality', '').lower()
        relationship_score = context.get('relationship_score', 0)
        
        if personality == 'sarah' and relationship_score > 60:
            suggestions.append({
                'theme': 'Neon Nights',
                'reason': "It matches our vibe together 💕",
                'type': 'relationship'
            })
        elif personality == 'xhash':
            suggestions.append({
                'theme': 'Cyber Dark',
                'reason': "Peak performance aesthetic",
                'type': 'personality'
            })
        
        # Remove duplicates and limit to 3
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s['theme'] not in seen:
                seen.add(s['theme'])
                unique_suggestions.append(s)
        
        return unique_suggestions[:3]
    
    @classmethod
    async def switch_theme(cls, user_id: str, theme_name: str, trigger: str = 'user_request', 
                          personality: str = None, message: str = None) -> bool:
        """Switch user theme and record interaction"""
        if theme_name not in cls.AVAILABLE_THEMES:
            return False
        
        try:
            # Get current preferences
            prefs = await cls.get_user_preferences(user_id)
            old_theme = prefs.get('preferred_theme', 'Cyber Dark')
            
            # Update theme history
            history = json.loads(prefs.get('theme_history', '[]')) if prefs.get('theme_history') else []
            history.append({
                'from': old_theme,
                'to': theme_name,
                'timestamp': datetime.now().isoformat(),
                'trigger': trigger
            })
            # Keep only last 10 changes
            history = history[-10:]
            
            # Update preferences
            await db.execute("""
                UPDATE user_preferences 
                SET preferred_theme = $2,
                    theme_history = $3::jsonb,
                    last_theme_change = CURRENT_TIMESTAMP,
                    theme_change_count = theme_change_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
            """, user_id, theme_name, json.dumps(history))
            
            # Record interaction
            await db.execute("""
                INSERT INTO theme_interactions 
                (user_id, theme_name, action, trigger, ai_personality, message)
                VALUES ($1, $2, 'switched', $3, $4, $5)
            """, user_id, theme_name, trigger, personality, message)
            
            return True
        except Exception as e:
            print(f"Error switching theme: {e}")
            return False
    
    @classmethod
    async def get_theme_by_category(cls, category: str) -> Optional[str]:
        """Get a random theme from category"""
        theme = await db.fetchrow("""
            SELECT theme_name FROM available_themes 
            WHERE category = $1 
            ORDER BY RANDOM() 
            LIMIT 1
        """, category)
        return theme['theme_name'] if theme else None
    
    @classmethod
    async def get_current_theme(cls, user_id: str) -> str:
        """Get user's current theme"""
        prefs = await cls.get_user_preferences(user_id)
        return prefs.get('preferred_theme', 'Cyber Dark')
    
    @classmethod
    async def should_suggest_theme(cls, user_id: str) -> bool:
        """Check if we should proactively suggest a theme"""
        # Check last theme change
        prefs = await db.fetchrow("""
            SELECT last_theme_change, theme_change_count 
            FROM user_preferences 
            WHERE user_id = $1
        """, user_id)
        
        if not prefs:
            return True
        
        # Suggest if hasn't changed theme in 7 days
        if prefs['last_theme_change']:
            days_since = (datetime.now() - prefs['last_theme_change']).days
            if days_since > 7:
                return True
        
        # Don't suggest too often
        recent_suggestions = await db.fetchval("""
            SELECT COUNT(*) FROM theme_interactions
            WHERE user_id = $1 
            AND action = 'suggested'
            AND timestamp > NOW() - INTERVAL '24 hours'
        """, user_id)
        
        return recent_suggestions < 2

theme_service = ThemeService()
