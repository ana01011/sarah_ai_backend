"""
Chat API routes
"""
from fastapi import APIRouter, HTTPException, Depends
from app.models.chat import ChatMessage, ChatResponse, PersonalityType, Conversation, Message
from app.models.auth import User
from app.core.database import db
from app.services.llm_service import llm_service
from app.agents.personalities.sarah import SarahAgent
from app.agents.personalities.xhash import XhashAgent
from app.agents.personalities.neutral import NeutralAgent
from app.api.v1.routers.auth_router import get_current_user_dependency
from typing import List, Optional
from uuid import uuid4
import time
import re

router = APIRouter()

# Initialize agents
agents = {
    PersonalityType.SARAH: SarahAgent(),
    PersonalityType.XHASH: XhashAgent(),
    PersonalityType.NEUTRAL: NeutralAgent()
}

async def extract_user_info(user_id: str, message: str):
    """Extract and store user information from message"""
    msg_lower = message.lower()
    
    # Extract name
    name_patterns = [
        r"(?:i am|i'm|im|my name is)\s+([A-Z][a-z]+)",
        r"(?:call me)\s+([A-Z][a-z]+)"
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            name = match.group(1)
            await db.execute("""
                UPDATE user_profiles 
                SET name = $2, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
            """, user_id, name)
            
            await db.execute("""
                INSERT INTO user_facts (user_id, fact_type, fact_value, source)
                VALUES ($1, 'name', $2, 'conversation')
                ON CONFLICT DO NOTHING
            """, user_id, name)
            break
    
    # Extract age
    age_match = re.search(r"(?:i am|i'm)\s+(\d+)\s*(?:years? old)?", msg_lower)
    if age_match:
        age = int(age_match.group(1))
        await db.execute("""
            UPDATE user_profiles 
            SET age = $2, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $1
        """, user_id, age)
        
        await db.execute("""
            INSERT INTO user_facts (user_id, fact_type, fact_value, source)
            VALUES ($1, 'age', $2, 'conversation')
            ON CONFLICT DO NOTHING
        """, user_id, str(age))
    
    # Detect gender
    if any(word in msg_lower for word in [" male", " man", " guy", " boy"]):
        await db.execute("""
            UPDATE user_profiles 
            SET gender = 'male', updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $1
        """, user_id)
    elif any(word in msg_lower for word in [" female", " woman", " girl", " lady"]):
        await db.execute("""
            UPDATE user_profiles 
            SET gender = 'female', updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $1
        """, user_id)

async def get_user_context(user_id: str) -> dict:
    """Get user context for personalization"""
    # Get user profile
    profile = await db.fetchrow("""
        SELECT name, age, gender, occupation, personality_preference
        FROM user_profiles
        WHERE user_id = $1
    """, user_id)
    
    # Get relationship info
    relationship = await db.fetchrow("""
        SELECT personality, relationship_score, stage, interaction_count
        FROM relationships
        WHERE user_id = $1
        ORDER BY last_interaction DESC
        LIMIT 1
    """, user_id)
    
    # Get recent messages for context
    recent_messages = await db.fetch("""
        SELECT role, content
        FROM messages
        WHERE user_id = $1
        ORDER BY created_at DESC
        LIMIT 5
    """, user_id)
    
    context = {}
    if profile:
        context.update(dict(profile))
    if relationship:
        context['relationship_score'] = relationship['relationship_score']
        context['relationship_stage'] = relationship['stage']
    if recent_messages:
        context['recent_messages'] = [dict(m) for m in recent_messages]
    
    return context

@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_message: ChatMessage,
    current_user: User = Depends(get_current_user_dependency)
):
    """Send a message and get AI response"""
    start_time = time.time()
    
    try:
        # Extract user information from message
        await extract_user_info(current_user.id, chat_message.message)
        
        # Get or create conversation
        if chat_message.conversation_id:
            conversation = await db.fetchrow("""
                SELECT * FROM conversations 
                WHERE id = $1 AND user_id = $2
            """, chat_message.conversation_id, current_user.id)
            
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            conversation_id = conversation['id']
        else:
            # Create new conversation
            conversation_id = uuid4()
            await db.execute("""
                INSERT INTO conversations (id, user_id, title)
                VALUES ($1, $2, $3)
            """, conversation_id, current_user.id, chat_message.message[:50])
        
        # Store user message
        user_message_id = uuid4()
        await db.execute("""
            INSERT INTO messages (id, conversation_id, user_id, role, content)
            VALUES ($1, $2, $3, 'user', $4)
        """, user_message_id, conversation_id, current_user.id, chat_message.message)
        
        # Get user context
        user_context = await get_user_context(current_user.id)
        
        # Determine personality
        personality = chat_message.personality
        if personality == PersonalityType.NEUTRAL and user_context.get('personality_preference'):
            personality = PersonalityType(user_context['personality_preference'])
        
        # Get appropriate agent
        agent = agents[personality]
        
        # Build prompt
        prompt = agent.build_prompt(chat_message.message, user_context)
        
        # Generate response
        response_text = llm_service.generate(
            prompt,
            max_tokens=chat_message.max_tokens,
            temperature=chat_message.temperature
        )
        
        # Store AI response
        ai_message_id = uuid4()
        await db.execute("""
            INSERT INTO messages (id, conversation_id, user_id, role, content, personality, tokens)
            VALUES ($1, $2, $3, 'assistant', $4, $5, $6)
        """, ai_message_id, conversation_id, current_user.id, response_text, personality.value, len(response_text.split()))
        
        # Update conversation
        await db.execute("""
            UPDATE conversations 
            SET last_message_at = CURRENT_TIMESTAMP, message_count = message_count + 2
            WHERE id = $1
        """, conversation_id)
        
        # Update or create relationship tracking
        await db.execute("""
            INSERT INTO relationships (user_id, personality, interaction_count, last_interaction)
            VALUES ($1, $2, 1, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, personality) 
            DO UPDATE SET 
                interaction_count = relationships.interaction_count + 1,
                relationship_score = LEAST(relationships.relationship_score + 2, 100),
                last_interaction = CURRENT_TIMESTAMP
        """, current_user.id, personality.value)
        
        processing_time = time.time() - start_time
        
        return ChatResponse(
            response=response_text,
            conversation_id=conversation_id,
            message_id=ai_message_id,
            personality=personality,
            tokens_used=len(response_text.split()),
            processing_time=processing_time,
            user_context=user_context
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations", response_model=List[Conversation])
async def get_conversations(
    current_user: User = Depends(get_current_user_dependency)
):
    """Get user's conversations"""
    conversations = await db.fetch("""
        SELECT * FROM conversations 
        WHERE user_id = $1 
        ORDER BY last_message_at DESC
        LIMIT 50
    """, current_user.id)
    
    return [Conversation(**dict(c)) for c in conversations]

@router.get("/conversations/{conversation_id}/messages", response_model=List[Message])
async def get_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user_dependency)
):
    """Get messages in a conversation"""
    # Verify conversation belongs to user
    conversation = await db.fetchrow("""
        SELECT * FROM conversations 
        WHERE id = $1 AND user_id = $2
    """, conversation_id, current_user.id)
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages = await db.fetch("""
        SELECT * FROM messages 
        WHERE conversation_id = $1 
        ORDER BY created_at ASC
    """, conversation_id)
    
    return [Message(**dict(m)) for m in messages]

@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user_dependency)
):
    """Delete a conversation"""
    result = await db.execute("""
        DELETE FROM conversations 
        WHERE id = $1 AND user_id = $2
    """, conversation_id, current_user.id)
    
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {"message": "Conversation deleted"}

@router.post("/personality")
async def set_personality_preference(
    personality: PersonalityType,
    current_user: User = Depends(get_current_user_dependency)
):
    """Set user's preferred personality"""
    await db.execute("""
        UPDATE user_profiles 
        SET personality_preference = $2, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = $1
    """, current_user.id, personality.value)
    
    return {"message": f"Personality preference set to {personality.value}"}
