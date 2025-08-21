import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from collections import deque

class MemoryManager:
    """Advanced memory management for Sarah AI"""
    
    def __init__(self, max_short_term: int = 50, max_long_term: int = 1000):
        # Short-term memory (session-based)
        self.short_term = deque(maxlen=max_short_term)
        
        # Long-term memory (persistent)
        self.long_term = {}
        
        # Working memory (current context)
        self.working_memory = {}
        
        # User profiles
        self.user_profiles = {}
        
        # Conversation threads
        self.conversation_threads = {}
        
    async def add_interaction(self, user_id: str, message: str, response: str, metadata: Dict = None):
        """Add interaction to memory"""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "message": message,
            "response": response,
            "metadata": metadata or {}
        }
        
        # Add to short-term
        self.short_term.append(interaction)
        
        # Update user profile
        await self.update_user_profile(user_id, interaction)
        
        # Extract important information for long-term storage
        await self.extract_long_term_memory(interaction)
        
    async def update_user_profile(self, user_id: str, interaction: Dict):
        """Update user profile based on interaction"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "created_at": datetime.now().isoformat(),
                "interaction_count": 0,
                "preferences": {},
                "topics": [],
                "personality_preference": None
            }
        
        profile = self.user_profiles[user_id]
        profile["interaction_count"] += 1
        profile["last_interaction"] = datetime.now().isoformat()
        
        # Extract preferences and topics
        # This is where you'd implement NLP to extract user preferences
        
    async def extract_long_term_memory(self, interaction: Dict):
        """Extract important information for long-term storage"""
        # Implement logic to identify important information
        # Examples: user preferences, learned facts, successful patterns
        pass
    
    async def get_relevant_context(self, message: str, user_id: str = None) -> Dict:
        """Get relevant context for current message"""
        context = {
            "recent_interactions": list(self.short_term)[-5:],
            "user_profile": self.user_profiles.get(user_id, {}),
            "related_memories": await self.search_memories(message)
        }
        return context
    
    async def search_memories(self, query: str) -> List[Dict]:
        """Search memories for relevant information"""
        # Implement semantic search through memories
        # For now, return recent relevant interactions
        relevant = []
        for interaction in self.short_term:
            if query.lower() in interaction["message"].lower():
                relevant.append(interaction)
        return relevant[:3]
    
    def get_conversation_summary(self) -> str:
        """Generate summary of recent conversation"""
        if not self.short_term:
            return "No recent conversation"
        
        # Generate summary from recent interactions
        summary = "Recent topics discussed: "
        topics = set()
        for interaction in list(self.short_term)[-10:]:
            # Extract topics (simplified version)
            words = interaction["message"].split()
            topics.update([w for w in words if len(w) > 5])
        
        return summary + ", ".join(list(topics)[:5])
