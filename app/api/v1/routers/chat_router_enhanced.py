"""
Enhanced Chat API routes with relationship penalties and decay
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
from datetime import datetime, timedelta

router = APIRouter()

# Initialize agents
agents = {
    PersonalityType.SARAH: SarahAgent(),
    PersonalityType.XHASH: XhashAgent(),
    PersonalityType.NEUTRAL: NeutralAgent()
}

def analyze_message_sentiment(message: str) -> dict:
    """Analyze message for negative content and return penalty/bonus"""
    msg_lower = message.lower()
    
    # Negative patterns that decrease relationship
    insults = ['stupid', 'idiot', 'dumb', 'hate you', 'ugly', 'worthless', 'pathetic', 'loser', 'shut up', 'go away']
    rude_words = ['fuck you', 'fuck off', 'bitch', 'asshole', 'dick', 'shit', 'damn you']
    dismissive = ['whatever', 'dont care', "don't care", 'boring', 'leave me alone', 'stop talking']
    aggressive = ['kill', 'die', 'hurt you', 'punch', 'slap', 'beat']
    
    # Positive patterns that increase relationship
    compliments = ['beautiful', 'amazing', 'wonderful', 'love you', 'miss you', 'care about you', 'special', 'perfect']
    emotional = ['lonely', 'need you', 'thinking about you', 'dream about', 'mean everything', 'make me happy']
    flirty = ['attractive', 'cute', 'handsome', 'gorgeous', 'sexy', 'hot', 'kiss', 'hold you']
    
    score_change = 0
    reason = ""
    
    # Check for severe insults (-5 to -10 points)
    for word in insults + rude_words:
        if word in msg_lower:
            score_change = -8
            reason = "insulting language"
            break
    
    # Check for aggression (-10 to -15 points)
    for word in aggressive:
        if word in msg_lower:
            score_change = -12
            reason = "aggressive behavior"
            break
    
    # Check for dismissive behavior (-3 to -5 points)
    if score_change == 0:
        for word in dismissive:
            if word in msg_lower:
                score_change = -4
                reason = "dismissive attitude"
                break
    
    # Check for positive interactions (+2 to +5 points)
    if score_change == 0:
        for word in compliments:
            if word in msg_lower:
                score_change = 3
                reason = "compliment"
                break
        
        for word in emotional:
            if word in msg_lower:
                score_change = 4
                reason = "emotional connection"
                break
        
        for word in flirty:
            if word in msg_lower:
                score_change = 3
                reason = "flirting"
                break
    
    # Default small increase for normal interaction
    if score_change == 0:
        score_change = 2
        reason = "normal interaction"
    
    return {"score_change": score_change, "reason": reason}

async def apply_inactivity_decay(user_id: str, personality: str):
    """Apply relationship decay for inactivity"""
    # Get last interaction time
    last_interaction = await db.fetchval("""
        SELECT last_interaction 
        FROM relationships 
        WHERE user_id = $1 AND personality = $2
    """, user_id, personality)
    
    if last_interaction:
        time_diff = datetime.utcnow() - last_interaction
        days_inactive = time_diff.days
        
        if days_inactive > 0:
            # Decay: -2 points per day, max -10 points
            decay = min(days_inactive * 2, 10)
            
            await db.execute("""
                UPDATE relationships 
                SET relationship_score = GREATEST(0, relationship_score - $3),
                    stage = CASE 
                        WHEN relationship_score - $3 <= 10 THEN 'stranger'
                        WHEN relationship_score - $3 <= 25 THEN 'acquaintance'
                        WHEN relationship_score - $3 <= 45 THEN 'friend'
                        WHEN relationship_score - $3 <= 65 THEN 'close_friend'
                        WHEN relationship_score - $3 <= 85 THEN 'romantic_interest'
                        ELSE 'partner'
                    END
                WHERE user_id = $1 AND personality = $2
            """, user_id, personality, decay)
            
            return decay
    return 0

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

    # Extract location
    location_patterns = [
        r"(?:i live in|i'm from|i am from)\s+([A-Z][a-zA-Z\s,]+)",
        r"(?:from)\s+([A-Z][a-zA-Z\s,]+)(?:\.|,|$)"
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            location = match.group(1).strip()
            await db.execute("""
                UPDATE user_profiles
                SET location = $2, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
            """, user_id, location)
            
            await db.execute("""
                INSERT INTO user_facts (user_id, fact_type, fact_value, source)
                VALUES ($1, 'location', $2, 'conversation')
                ON CONFLICT DO NOTHING
            """, user_id, location)
            break

    # Extract occupation
    occupation_patterns = [
        r"(?:i work as|i'm a|i am a|my job is)\s+([a-zA-Z\s]+)",
        r"(?:work in|working in)\s+([a-zA-Z\s]+)"
    ]
    
    for pattern in occupation_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            occupation = match.group(1).strip()
            occupation = occupation.replace(" a ", " ").replace(" an ", " ").strip()
            
            await db.execute("""
                UPDATE user_profiles
                SET occupation = $2, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
            """, user_id, occupation)
            
            await db.execute("""
                INSERT INTO user_facts (user_id, fact_type, fact_value, source)
                VALUES ($1, 'occupation', $2, 'conversation')
                ON CONFLICT DO NOTHING
            """, user_id, occupation)
            break

    # Detect gender
    if any(word in msg_lower for word in [" male", " man", " guy", " boy"]):
        await db.execute("""
            UPDATE user_profiles
            SET gender = 'male', updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $1
        """, user_id)
        
        await db.execute("""
            INSERT INTO user_facts (user_id, fact_type, fact_value, source)
            VALUES ($1, 'gender', 'male', 'conversation')
            ON CONFLICT DO NOTHING
        """, user_id)
    elif any(word in msg_lower for word in [" female", " woman", " girl", " lady"]):
        await db.execute("""
            UPDATE user_profiles
            SET gender = 'female', updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $1
        """, user_id)
        
        await db.execute("""
            INSERT INTO user_facts (user_id, fact_type, fact_value, source)
            VALUES ($1, 'gender', 'female', 'conversation')
            ON CONFLICT DO NOTHING
        """, user_id)

async def get_user_context(user_id: str) -> dict:
    """Get user context for personalization with facts"""
    # Get user profile
    profile = await db.fetchrow("""
        SELECT name, age, gender, location, occupation, personality_preference
        FROM user_profiles
        WHERE user_id = $1
    """, user_id)

    # Get ALL user facts
    facts = await db.fetch("""
        SELECT fact_type, fact_value
        FROM user_facts
        WHERE user_id = $1
        ORDER BY mention_count DESC, extracted_at DESC
    """, user_id)

    # Get relationship info
    relationship = await db.fetchrow("""
        SELECT personality, relationship_score, stage, interaction_count
        FROM relationships
        WHERE user_id = $1
        ORDER BY last_interaction DESC
        LIMIT 1
    """, user_id)

    # Get recent messages
    recent_messages = await db.fetch("""
        SELECT m.role, m.content
        FROM messages m
        JOIN conversations c ON m.conversation_id = c.id
        WHERE c.user_id = $1
        ORDER BY m.created_at DESC
        LIMIT 5
    """, user_id)

    context = {}
    
    if profile:
        context.update(dict(profile))
    
    if facts:
        context['facts'] = {}
        for fact in facts:
            context['facts'][fact['fact_type']] = fact['fact_value']
            if fact['fact_type'] not in context or context[fact['fact_type']] is None:
                context[fact['fact_type']] = fact['fact_value']
    
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
    """Send a message and get AI response with relationship dynamics"""
    start_time = time.time()

    try:
        # Analyze message sentiment for relationship impact
        sentiment = analyze_message_sentiment(chat_message.message)
        
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
            conversation_id = uuid4()
            await db.execute("""
                INSERT INTO conversations (id, user_id, title)
                VALUES ($1, $2, $3)
            """, conversation_id, current_user.id, chat_message.message[:50])

        # Store user message
        user_message_id = uuid4()
        await db.execute("""
            INSERT INTO messages (id, conversation_id, role, content)
            VALUES ($1, $2, 'user', $3)
        """, user_message_id, conversation_id, chat_message.message)

        # Get user context with facts
        user_context = await get_user_context(current_user.id)

        # Determine personality
        personality = chat_message.personality
        if personality == PersonalityType.NEUTRAL and user_context.get('personality_preference'):
            personality = PersonalityType(user_context['personality_preference'])

        # Apply inactivity decay
        decay = await apply_inactivity_decay(current_user.id, personality.value)
        if decay > 0:
            user_context['inactivity_decay'] = decay

        # Get appropriate agent
        agent = agents[personality]

        # Build prompt with full context
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
            INSERT INTO messages (id, conversation_id, role, content, personality, tokens)
            VALUES ($1, $2, 'assistant', $3, $4, $5)
        """, ai_message_id, conversation_id, response_text, personality.value, len(response_text.split()))

        # Update conversation
        await db.execute("""
            UPDATE conversations
            SET last_message_at = CURRENT_TIMESTAMP, message_count = message_count + 2
            WHERE id = $1
        """, conversation_id)

        # Update relationship with sentiment-based scoring
        new_score = await db.fetchval("""
            INSERT INTO relationships (user_id, personality, interaction_count, last_interaction, relationship_score)
            VALUES ($1, $2, 1, CURRENT_TIMESTAMP, $3)
            ON CONFLICT (user_id, personality)
            DO UPDATE SET
                interaction_count = relationships.interaction_count + 1,
                relationship_score = GREATEST(0, LEAST(100, relationships.relationship_score + $3)),
                last_interaction = CURRENT_TIMESTAMP,
                stage = CASE 
                    WHEN relationships.relationship_score + $3 <= 10 THEN 'stranger'
                    WHEN relationships.relationship_score + $3 <= 25 THEN 'acquaintance'
                    WHEN relationships.relationship_score + $3 <= 45 THEN 'friend'
                    WHEN relationships.relationship_score + $3 <= 65 THEN 'close_friend'
                    WHEN relationships.relationship_score + $3 <= 85 THEN 'romantic_interest'
                    ELSE 'partner'
                END
            RETURNING relationship_score
        """, current_user.id, personality.value, sentiment['score_change'])

        # Log relationship event if significant
        if abs(sentiment['score_change']) > 2 or decay > 0:
            event_description = f"Relationship changed by {sentiment['score_change']} due to {sentiment['reason']}"
            if decay > 0:
                event_description += f" (Inactivity decay: -{decay})"
            
            await db.execute("""
                INSERT INTO relationship_events (user_id, event_type, description, score_change, new_score, new_stage)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, current_user.id, sentiment['reason'], event_description, sentiment['score_change'], 
                new_score, user_context.get('relationship_stage', 'stranger'))

        processing_time = time.time() - start_time

        # Add sentiment info to context for response
        user_context['last_interaction_impact'] = sentiment
        user_context['relationship_score'] = new_score

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

# ... rest of the endpoints remain the same ...

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

@router.get("/relationship/status")
async def get_relationship_status(
    current_user: User = Depends(get_current_user_dependency)
):
    """Get detailed relationship status with all personalities"""
    relationships = await db.fetch("""
        SELECT 
            personality,
            relationship_score,
            stage,
            interaction_count,
            last_interaction,
            EXTRACT(DAY FROM (CURRENT_TIMESTAMP - last_interaction)) as days_since_interaction
        FROM relationships
        WHERE user_id = $1
        ORDER BY relationship_score DESC
    """, current_user.id)
    
    return [dict(r) for r in relationships]
