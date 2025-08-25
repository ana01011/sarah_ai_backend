"""
Enhanced Memory System for Sarah AI
This replaces the chat_with_memory function with a robust context-aware version
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional

# Global memory with better structure
USER_MEMORY = {}
USER_CONTEXT = {}  # Stores extracted facts about users

def extract_user_facts(message: str, user_id: str):
    """Extract and remember important facts from conversation"""
    message_lower = message.lower()
    
    if user_id not in USER_CONTEXT:
        USER_CONTEXT[user_id] = {
            "name": None,
            "preferences": [],
            "topics": [],
            "facts": []
        }
    
    # Extract name
    if "my name is" in message_lower or "i am" in message_lower or "i'm" in message_lower:
        import re
        name_match = re.search(r"(?:my name is|i am|i'm)\s+([A-Z][a-z]+)", message, re.IGNORECASE)
        if name_match:
            USER_CONTEXT[user_id]["name"] = name_match.group(1)
    
    # Store important facts
    if any(word in message_lower for word in ["like", "love", "hate", "prefer", "favorite"]):
        USER_CONTEXT[user_id]["preferences"].append(message)
    
    # Store topics discussed
    important_words = [w for w in message.split() if len(w) > 5]
    USER_CONTEXT[user_id]["topics"].extend(important_words[:3])

def build_context_prompt(user_id: str, current_message: str, memory: List[Dict]) -> str:
    """Build a comprehensive context-aware prompt"""
    
    # Start with system instruction
    prompt = "You are Sarah AI, a helpful and memory-enabled assistant. "
    
    # Add user-specific context if available
    if user_id in USER_CONTEXT:
        ctx = USER_CONTEXT[user_id]
        if ctx["name"]:
            prompt += f"You are talking to {ctx['name']}. "
        if ctx["preferences"]:
            prompt += f"You remember they mentioned: {ctx['preferences'][-1]}. "
    
    prompt += "\n\n"
    
    # Add conversation history with clear formatting
    if memory and len(memory) > 0:
        prompt += "### Previous Conversation ###\n"
        # Use ALL available context (not just last 2-3)
        for i, exchange in enumerate(memory[-7:], 1):  # Last 7 exchanges
            prompt += f"[Turn {i}]\n"
            prompt += f"Human: {exchange['user']}\n"
            prompt += f"Sarah: {exchange['assistant']}\n"
            prompt += "\n"
        
        prompt += "### Current Turn ###\n"
        prompt += f"[Turn {len(memory[-7:]) + 1}]\n"
        prompt += f"Human: {current_message}\n"
        prompt += "Sarah: [Continue the conversation naturally, remembering all context above]"
    else:
        prompt += f"Human: {current_message}\n"
        prompt += "Sarah:"
    
    return prompt

async def chat_with_enhanced_memory(request):
    """Enhanced chat with robust memory and context"""
    start = time.time()
    user_id = request.user_id or "default"
    
    # Initialize memory if needed
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = []
    
    # Extract facts from current message
    extract_user_facts(request.message, user_id)
    
    # Check for identity question
    if is_identity_question(request.message):
        response_text = "I'm Sarah AI, an independent AI assistant created by independent developers."
    else:
        # Build comprehensive prompt
        prompt = build_context_prompt(user_id, request.message, USER_MEMORY[user_id])
        
        # Debug: Print the prompt
        print("\n" + "="*60)
        print("PROMPT BEING SENT TO MODEL:")
        print(prompt)
        print("="*60 + "\n")
        
        # Generate response with higher token limit for context
        response = model(
            prompt,
            max_tokens=min(request.max_tokens, 200),  # Allow longer responses
            temperature=request.temperature,
            top_k=40,
            top_p=0.95,
            repeat_penalty=1.1,
            stop=["Human:", "[Turn", "###", "\n\n\n"],
            echo=False
        )
        
        response_text = response['choices'][0]['text'].strip()
        
        # Clean the response
        response_text = clean_response(response_text)
        
        # Remove any accidental continuations
        response_text = response_text.split("Human:")[0].strip()
        response_text = response_text.split("Sarah:")[0].strip()
    
    # Store the exchange in memory with timestamp
    USER_MEMORY[user_id].append({
        "user": request.message,
        "assistant": response_text,
        "timestamp": datetime.now().isoformat(),
        "context": USER_CONTEXT.get(user_id, {})
    })
    
    # Keep last 15 exchanges for better context
    if len(USER_MEMORY[user_id]) > 15:
        USER_MEMORY[user_id] = USER_MEMORY[user_id][-15:]
    
    elapsed = time.time() - start
    
    return {
        "response": response_text,
        "user_id": user_id,
        "memory_size": len(USER_MEMORY[user_id]),
        "context": USER_CONTEXT.get(user_id, {}),
        "stats": {
            "time": round(elapsed, 3),
            "context_used": True,
            "exchanges_in_memory": len(USER_MEMORY[user_id]),
            "tokens_per_second": round(len(response_text.split())/elapsed, 1) if elapsed > 0 else 0
        }
    }

# Debug endpoint to check memory
async def get_full_memory(user_id: str):
    """Get complete memory and context for debugging"""
    return {
        "user_id": user_id,
        "conversation_memory": USER_MEMORY.get(user_id, []),
        "user_context": USER_CONTEXT.get(user_id, {}),
        "total_exchanges": len(USER_MEMORY.get(user_id, []))
    }
