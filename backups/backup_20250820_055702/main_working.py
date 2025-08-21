"""
WORKING Memory System - Actually Uses Stored Data!
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
import time
import json
import re
import os
from typing import Optional, Dict

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🚀 Loading WORKING Memory System...")
model = Llama(
    model_path="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
    n_ctx=1024,
    n_threads=4,
    n_batch=256,
    use_mmap=True,
    verbose=False
)
print("✅ Model Ready!")

# Load existing memory files
def load_json_file(filename):
    try:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def save_json_file(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    except:
        pass

# Load both memory systems
USER_MEMORY = load_json_file("user_memory.json")
USER_PROFILES = load_json_file("relationship_profiles.json")

print(f"📚 Loaded {len(USER_MEMORY)} memories, {len(USER_PROFILES)} profiles")

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    agent_role: Optional[str] = "general"
    max_tokens: int = 200
    temperature: float = 0.8

def get_user_info(user_id: str) -> Dict:
    """Get all stored info about a user"""
    info = {
        "name": None,
        "age": None,
        "gender": "unknown",
        "score": 0,
        "conversations": []
    }
    
    # Get from profiles
    if user_id in USER_PROFILES:
        profile = USER_PROFILES[user_id]
        if "personal_info" in profile:
            info["name"] = profile["personal_info"].get("name")
            info["age"] = profile["personal_info"].get("age")
        info["gender"] = profile.get("gender", "unknown")
        info["score"] = profile.get("score", 0)
    
    # Get conversations from memory
    if user_id in USER_MEMORY:
        convos = USER_MEMORY[user_id]
        if isinstance(convos, list):
            info["conversations"] = convos[-5:]  # Last 5 conversations
    
    return info

def update_user_info(user_id: str, message: str, response: str, info: Dict):
    """Update user information from message"""
    msg_lower = message.lower()
    
    # Initialize profile if needed
    if user_id not in USER_PROFILES:
        USER_PROFILES[user_id] = {
            "user_id": user_id,
            "gender": "unknown",
            "score": 0,
            "personal_info": {},
            "interaction_history": []
        }
    
    profile = USER_PROFILES[user_id]
    
    # Extract name
    name_match = re.search(r"(?:i am|i'm|im|my name is)\s+([A-Z][a-z]+)", message, re.IGNORECASE)
    if name_match:
        name = name_match.group(1)
        if "personal_info" not in profile:
            profile["personal_info"] = {}
        profile["personal_info"]["name"] = name
        profile["score"] = profile.get("score", 0) + 10
        print(f"📝 Stored name: {name} for {user_id}")
    
    # Extract age
    age_match = re.search(r"(\d{1,3})\s*(?:years? old|yo|yr)", msg_lower)
    if age_match:
        age = int(age_match.group(1))
        if "personal_info" not in profile:
            profile["personal_info"] = {}
        profile["personal_info"]["age"] = age
        profile["score"] = profile.get("score", 0) + 5
        print(f"📝 Stored age: {age} for {user_id}")
    
    # Detect gender
    if any(word in msg_lower for word in [" male", " man", " guy", " boy"]):
        profile["gender"] = "male"
        profile["score"] = profile.get("score", 0) + 5
    elif any(word in msg_lower for word in [" female", " woman", " girl"]):
        profile["gender"] = "female"
        profile["score"] = profile.get("score", 0) + 5
    
    # Update score
    profile["score"] = min(100, profile.get("score", 0) + 1)
    
    # Store conversation
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = []
    
    USER_MEMORY[user_id].append({
        "user": message,
        "assistant": response,
        "timestamp": time.time()
    })
    
    # Keep only last 10 conversations
    if len(USER_MEMORY[user_id]) > 10:
        USER_MEMORY[user_id] = USER_MEMORY[user_id][-10:]
    
    # Save both files
    save_json_file("user_memory.json", USER_MEMORY)
    save_json_file("relationship_profiles.json", USER_PROFILES)

@app.post("/api/chat/with-memory")
async def chat_with_memory(request: ChatRequest):
    start = time.time()
    user_id = request.user_id or f"user_{int(time.time()*1000)}"
    
    # Get stored user info
    user_info = get_user_info(user_id)
    
    # Handle special questions FIRST
    msg_lower = request.message.lower()
    
    if "what is my name" in msg_lower or "what's my name" in msg_lower or "who am i" in msg_lower:
        if user_info["name"]:
            if user_info["gender"] == "male":
                response_text = f"Your name is {user_info['name']}, silly! Did you forget? 😏"
            elif user_info["gender"] == "female":
                response_text = f"You're {user_info['name']}, beautiful."
            else:
                response_text = f"Your name is {user_info['name']}."
        else:
            response_text = "You haven't told me your name yet. What should I call you?"
    
    elif "how old am i" in msg_lower or "what's my age" in msg_lower:
        if user_info["age"]:
            response_text = f"You're {user_info['age']} years old."
        else:
            response_text = "You haven't told me your age yet."
    
    else:
        # Build context for AI
        context = []
        if user_info["name"]:
            context.append(f"The user's name is {user_info['name']}")
        if user_info["age"]:
            context.append(f"They are {user_info['age']} years old")
        if user_info["gender"] != "unknown":
            context.append(f"They are {user_info['gender']}")
        
        context_str = ". ".join(context) + "." if context else ""
        
        # Build conversation history
        history = ""
        for conv in user_info["conversations"][-3:]:
            history += f"User: {conv['user']}\n"
            history += f"Assistant: {conv['assistant']}\n"
        
        # Select personality
        if user_info["gender"] == "male":
            personality = f"You are Sarah, a confident woman talking to {user_info['name'] or 'a man'}. Be friendly with a touch of sass."
        elif user_info["gender"] == "female":
            personality = f"You are Xhash, a charming man talking to {user_info['name'] or 'a woman'}. Be attentive and engaging."
        else:
            personality = "You are a helpful AI assistant."
        
        # Generate response
        prompt = f"""{personality}
{context_str}

Recent conversation:
{history}

User: {request.message}
Assistant:"""
        
        response = model(
            prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=["User:", "\n\n"],
            echo=False
        )
        
        response_text = response['choices'][0]['text'].strip()
    
    # Update user info with new data
    update_user_info(user_id, request.message, response_text, user_info)
    
    # Get updated info for response
    updated_info = get_user_info(user_id)
    
    return {
        "response": response_text,
        "user_id": user_id,
        "memory_size": len(updated_info["conversations"]),
        "relationship": {
            "persona": "sarah" if updated_info["gender"] == "male" else "xhash" if updated_info["gender"] == "female" else "neutral",
            "stage": "Stranger" if updated_info["score"] < 30 else "Friend" if updated_info["score"] < 60 else "Close",
            "score": updated_info["score"]
        },
        "stats": {
            "time": round(time.time() - start, 2),
            "context_used": bool(user_info["conversations"])
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "name": "Working Memory System",
        "users_with_memory": len(USER_MEMORY),
        "users_with_profiles": len(USER_PROFILES)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
