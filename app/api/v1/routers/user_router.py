"""
User API routes
"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.auth import User
from app.core.database import db
from app.api.v1.routers.auth_router import get_current_user_dependency
from typing import Dict, Any, List
from pydantic import BaseModel

router = APIRouter()

class UserProfile(BaseModel):
    name: str = None
    age: int = None
    gender: str = None
    occupation: str = None
    location: str = None

class UserStats(BaseModel):
    total_conversations: int
    total_messages: int
    favorite_personality: str
    relationship_scores: Dict[str, int]

@router.get("/profile")
async def get_profile(current_user: User = Depends(get_current_user_dependency)):
    """Get user profile"""
    profile = await db.fetchrow("""
        SELECT * FROM user_profiles WHERE user_id = $1
    """, current_user.id)
    
    if not profile:
        # Create default profile
        await db.execute("""
            INSERT INTO user_profiles (user_id, personality_preference)
            VALUES ($1, 'neutral')
        """, current_user.id)
        profile = await db.fetchrow("""
            SELECT * FROM user_profiles WHERE user_id = $1
        """, current_user.id)
    
    return dict(profile)

@router.put("/profile")
async def update_profile(
    profile_data: UserProfile,
    current_user: User = Depends(get_current_user_dependency)
):
    """Update user profile"""
    updates = []
    values = [current_user.id]
    idx = 2
    
    for field, value in profile_data.dict(exclude_none=True).items():
        updates.append(f"{field} = ${idx}")
        values.append(value)
        idx += 1
    
    if updates:
        query = f"""
            UPDATE user_profiles 
            SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $1
        """
        await db.execute(query, *values)
    
    return {"message": "Profile updated"}

@router.get("/facts")
async def get_user_facts(current_user: User = Depends(get_current_user_dependency)):
    """Get extracted facts about user"""
    facts = await db.fetch("""
        SELECT fact_type, fact_value, confidence, created_at
        FROM user_facts
        WHERE user_id = $1
        ORDER BY created_at DESC
    """, current_user.id)
    
    return [dict(f) for f in facts]

@router.get("/stats", response_model=UserStats)
async def get_user_stats(current_user: User = Depends(get_current_user_dependency)):
    """Get user statistics"""
    # Get conversation count
    conv_count = await db.fetchval("""
        SELECT COUNT(*) FROM conversations WHERE user_id = $1
    """, current_user.id)
    
    # Get message count
    msg_count = await db.fetchval("""
        SELECT COUNT(*) FROM messages WHERE user_id = $1
    """, current_user.id)
    
    # Get favorite personality
    fav_personality = await db.fetchval("""
        SELECT personality, COUNT(*) as count
        FROM messages
        WHERE user_id = $1 AND personality IS NOT NULL
        GROUP BY personality
        ORDER BY count DESC
        LIMIT 1
    """, current_user.id)
    
    # Get relationship scores
    relationships = await db.fetch("""
        SELECT personality, relationship_score
        FROM relationships
        WHERE user_id = $1
    """, current_user.id)
    
    rel_scores = {r['personality']: r['relationship_score'] for r in relationships}
    
    return UserStats(
        total_conversations=conv_count or 0,
        total_messages=msg_count or 0,
        favorite_personality=fav_personality or "neutral",
        relationship_scores=rel_scores
    )

@router.delete("/account")
async def delete_account(current_user: User = Depends(get_current_user_dependency)):
    """Delete user account and all data"""
    # Delete user (cascades to all related data)
    await db.execute("DELETE FROM users WHERE id = $1", current_user.id)
    
    return {"message": "Account deleted successfully"}
