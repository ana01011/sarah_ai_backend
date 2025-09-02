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

    # Theme categories for better organization
    THEME_CATEGORIES = {
        'dark': ['Cyber Dark', 'Simple Dark', 'Developer Dark', 'Backend Slate', 'Deep Ocean'],
        'light': ['Pure Light', 'Simple Light', 'Frontend Pink'],
        'colorful': ['Neon Nights', 'Tech Blue', 'Marketing Purple', 'Product Teal', 'Data Cyan'],
        'professional': ['Simple Dark', 'Simple Light', 'Tech Blue', 'Finance Green'],
        'coding': ['Developer Dark', 'Backend Slate', 'Cyber Dark', 'AI Neural'],
        'fun': ['Neon Nights', 'Frontend Pink', 'Marketing Purple'],
        'work': ['Finance Green', 'Tech Blue', 'Product Teal']
    }

    # Theme descriptions
    THEME_DESCRIPTIONS = {
        'Cyber Dark': 'Futuristic dark theme with neon accents',
        'Pure Light': 'Clean, minimalist light theme',
        'Neon Nights': 'Vibrant colors with dark background',
        'Deep Ocean': 'Calming blue tones',
        'Simple Dark': 'Classic dark mode',
        'Simple Light': 'Classic light mode',
        'Tech Blue': 'Professional blue accent theme',
        'Finance Green': 'Money-focused green theme',
        'Marketing Purple': 'Creative purple theme',
        'Product Teal': 'Product-focused teal theme',
        'Developer Dark': 'Optimized for coding',
        'AI Neural': 'AI-inspired neural network theme',
        'Frontend Pink': 'Playful pink for frontend devs',
        'Backend Slate': 'Serious slate for backend work',
        'Data Cyan': 'Data visualization cyan theme'
    }

    # Theme aliases for natural language
    THEME_ALIASES = {
        'dark mode': 'Simple Dark',
        'light mode': 'Pure Light',
        'night': 'Developer Dark',
        'day': 'Simple Light',
        'hacker': 'Cyber Dark',
        'ocean': 'Deep Ocean',
        'professional': 'Tech Blue',
        'fun': 'Neon Nights'
    }

    # Smart aliases for mood-based suggestions
    SMART_ALIASES = {
        'professional': ['Tech Blue', 'Finance Green', 'Simple Light'],
        'fun': ['Neon Nights', 'Frontend Pink', 'Marketing Purple'],
        'serious': ['Backend Slate', 'Simple Dark', 'Developer Dark'],
        'creative': ['Marketing Purple', 'Frontend Pink', 'Neon Nights'],
        'relaxing': ['Deep Ocean', 'Pure Light', 'Simple Light'],
        'energetic': ['Neon Nights', 'Data Cyan', 'Tech Blue']
    }

    def detect_theme_command(self, message: str) -> Optional[tuple]:
        """Detect theme-related commands in user message"""
        msg_lower = message.lower()
        
        # Simple detection for dark/light requests
        if 'dark' in msg_lower:
            # Check for dark theme requests in various forms
            if any(word in msg_lower for word in ['background', 'theme', 'mode', 'color', 'switch', 'change', 'make', 'want', 'use', 'set']):
                return ('switch_theme', 'Simple Dark', 'User requested dark theme')
        
        if 'light' in msg_lower or 'bright' in msg_lower:
            # Check for light theme requests
            if any(word in msg_lower for word in ['background', 'theme', 'mode', 'color', 'switch', 'change', 'make', 'want', 'use', 'set']):
                return ('switch_theme', 'Pure Light', 'User requested light theme')
        
        # Direct theme name detection
        for theme in self.AVAILABLE_THEMES:
            theme_lower = theme.lower()
            if (theme_lower in msg_lower or 
                f"{theme_lower} theme" in msg_lower or
                f"{theme_lower} mode" in msg_lower):
                return ('switch_theme', theme, f'User requested {theme}')

        # Check for partial matches (e.g., "Pure Light" when user says "pure light")
        words = msg_lower.split()
        for theme in self.AVAILABLE_THEMES:
            theme_words = theme.lower().split()
            # Check if all words of theme name are in message
            if all(word in words for word in theme_words):
                return ('switch_theme', theme, f'User requested {theme}')

        # Check for theme query
        if any(phrase in msg_lower for phrase in ['what theme', 'which theme', 'current theme', 'my theme', 'theme am i']):
            return ('query_theme', None, 'User asked about current theme')

        # Check for theme suggestions
        if any(phrase in msg_lower for phrase in ['suggest theme', 'recommend theme', 'best theme', 'good theme']):
            return ('suggest_theme', None, 'User wants theme suggestions')

        # Check aliases
        for alias, theme_name in self.THEME_ALIASES.items():
            if alias in msg_lower:
                return ('switch_theme', theme_name, f'User requested {theme_name} via alias')

        return None

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
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

    async def suggest_theme_based_on_context(self, user_id: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
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

    async def switch_theme(self, user_id: str, theme_name: str, trigger: str = 'user_request',
                          personality: str = None, message: str = None) -> bool:
        """Switch user theme and record interaction"""
        if theme_name not in self.AVAILABLE_THEMES:
            return False

        try:
            # Get current preferences
            prefs = await self.get_user_preferences(user_id)
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

    async def get_theme_by_category(self, category: str) -> Optional[str]:
        """Get a random theme from category"""
        theme = await db.fetchrow("""
            SELECT theme_name FROM available_themes
            WHERE category = $1
            ORDER BY RANDOM()
            LIMIT 1
        """, category)
        return theme['theme_name'] if theme else None

    async def get_current_theme(self, user_id: str) -> str:
        """Get user's current theme"""
        prefs = await self.get_user_preferences(user_id)
        return prefs.get('preferred_theme', 'Cyber Dark')

    async def should_suggest_theme(self, user_id: str) -> bool:
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

    async def get_themes_by_category(self, category: str) -> List[Dict[str, str]]:
        """Get themes in a specific category with descriptions"""
        themes = self.THEME_CATEGORIES.get(category, [])
        return [
            {
                'theme': theme,
                'description': self.THEME_DESCRIPTIONS.get(theme, '')
            }
            for theme in themes
        ]

    async def get_theme_suggestions(self, user_id: str, context: Dict[str, Any]) -> List[str]:
        """Get theme suggestions based on context"""
        suggestions = await self.suggest_theme_based_on_context(user_id, context)
        return [s['theme'] for s in suggestions]

    async def suggest_themes_for_mood(self, mood: str) -> List[str]:
        """Suggest themes based on user's mood or activity"""
        mood_lower = mood.lower()

        # Check direct mood mappings
        if mood_lower in self.SMART_ALIASES:
            return self.SMART_ALIASES[mood_lower][:3]

        # Check categories
        if mood_lower in self.THEME_CATEGORIES:
            return self.THEME_CATEGORIES[mood_lower][:3]

        # Fuzzy matching for moods
        suggestions = []
        if 'dark' in mood_lower or 'night' in mood_lower:
            suggestions = self.THEME_CATEGORIES['dark'][:3]
        elif 'light' in mood_lower or 'bright' in mood_lower:
            suggestions = self.THEME_CATEGORIES['light'][:3]
        elif 'color' in mood_lower or 'fun' in mood_lower:
            suggestions = self.THEME_CATEGORIES['colorful'][:3]
        elif 'work' in mood_lower or 'professional' in mood_lower:
            suggestions = self.THEME_CATEGORIES['professional'][:3]
        elif 'code' in mood_lower or 'coding' in mood_lower:
            suggestions = self.THEME_CATEGORIES['coding'][:3]
        else:
            # Default suggestions
            suggestions = ['Cyber Dark', 'Pure Light', 'Neon Nights']

        return suggestions

    async def detect_theme_intent(self, message: str) -> Optional[Tuple[str, Any, str]]:
        """Enhanced theme detection with categories and moods"""
        msg_lower = message.lower()

        # Check for category requests
        if 'show' in msg_lower or 'list' in msg_lower or 'what themes' in msg_lower:
            for category in self.THEME_CATEGORIES.keys():
                if category in msg_lower:
                    themes = await self.get_themes_by_category(category)
                    return ('show_category', themes, f'Showing {category} themes')

            # Show all themes if no specific category
            if 'all themes' in msg_lower or 'available themes' in msg_lower:
                return ('show_all', self.AVAILABLE_THEMES, 'Showing all themes')

        # Check for mood-based requests
        if any(word in msg_lower for word in ['something', 'theme for', 'good for', 'want something']):
            # Extract the mood/activity
            for mood in ['professional', 'fun', 'coding', 'reading', 'working', 'night', 'day']:
                if mood in msg_lower:
                    suggestions = await self.suggest_themes_for_mood(mood)
                    return ('mood_suggestion', suggestions, f'Themes for {mood}')

        # Use the standard detection for direct theme commands
        return self.detect_theme_command(message)


theme_service = ThemeService()
