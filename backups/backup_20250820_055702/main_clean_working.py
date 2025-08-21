"""
CLEAN Working Version - Handles Both Memory Formats
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
import json
import os
import time
import re
from typing import Optional

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🚀 Loading Clean Working Version...")
model = Llama(
    model_path="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
    n_ctx=1024,
    n_threads=4,
    n_batch=256,
    use_mmap=True,
    verbose=False
)
print("✅ Model Ready!")

# Load and fix memory formats
PROFILES = {}
MEMORY = {}

if os.path.exists("relationship_profiles.json"):
    with open("relationship_profiles.json", 'r') as f:
        PROFILES = json.load(f)
        print(f"📚 Loaded {len(PROFILES)} profiles")

if os.path.exists("user_memory.json"):
    with open("user_memory.json", 'r') as f:
        raw_memory = json.load(f)
        # Fix memory format - ensure all are lists
        for user_id, mem in raw_memory.items():
            if isinstance(mem, list):
                MEMORY[user_id] = mem
            elif isinstance(mem, dict):
                # Convert dict to list format
                MEMORY[user_id] = []
            else:
                MEMORY[user_id] = []
        print(f"📚 Fixed and loaded {len(MEMORY)} user memories")

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    agent_role: Optional[str] = "general"
    max_tokens: int = 200
    temperature: float = 0.8

@app.post("/api/chat/with-memory")
async def chat_with_memory(request: ChatRequest):
    start = time.time()
    user_id = request.user_id or f"user_{int(time.time()*1000)}"
    msg_lower = request.message.lower()
    
    # Get user profile
    user_name = None
    user_age = None
    user_gender = "unknown"
    user_score = 0
    
    if user_id in PROFILES:
        profile = PROFILES[user_id]
        personal_info = profile.get("personal_info", {})
        user_name = personal_info.get("name")
        user_age = personal_info.get("age")
        user_gender = profile.get("gender", "unknown")
        user_score = profile.get("score", 0)
        print(f"Found {user_id}: name={user_name}, gender={user_gender}, score={user_score}")
    
    # Special questions
    if any(phrase in msg_lower for phrase in ["what is my name", "what's my name", "who am i"]):
        if user_name:
            if user_gender == "male":
                response_text = f"Your name is {user_name}! Come on, you know that! 😊"
            else:
                response_text = f"Your name is {user_name}."
        else:
            response_text = "You haven't told me your name yet. What should I call you?"
    
    elif "how old" in msg_lower and "i" in msg_lower:
        if user_age:
            response_text = f"You're {user_age} years old."
        else:
            response_text = "You haven't told me your age."
    
    elif "remember" in msg_lower or "know about me" in msg_lower:
        facts = []
        if user_name:
            facts.append(f"your name is {user_name}")
        if user_age:
            facts.append(f"you're {user_age}")
        if user_gender != "unknown":
            facts.append(f"you're {user_gender}")
        
        if facts:
            response_text = f"Of course! I know {', '.join(facts)}."
        else:
            response_text = "Tell me about yourself!"
    
    else:
        # Extract new info
        name_match = re.search(r"(?:i am|i'm|im|my name is)\s+([A-Z][a-z]+)", request.message, re.IGNORECASE)
        if name_match:
            new_name = name_match.group(1)
            if user_id not in PROFILES:
                PROFILES[user_id] = {"personal_info": {}, "gender": "unknown", "score": 0}
            PROFILES[user_id]["personal_info"]["name"] = new_name
            user_name = new_name
            print(f"Stored name: {new_name}")
        
        # Generate response
        context = f"Talking to {user_name}. " if user_name else ""
        
        if user_gender == "male":
            personality = f"You are Sarah, a friendly woman. {context}"
        elif user_gender == "female":
            personality = f"You are Xhash, a charming man. {context}"
        else:
            personality = f"You are a helpful assistant. {context}"
        
        prompt = f"{personality}\n\nUser: {request.message}\nAssistant:"
        
        response = model(
            prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=["User:", "\n\n"],
            echo=False
        )
        
        response_text = response['choices'][0]['text'].strip()
    
    # Update memory (ensure it's a list)
    if user_id not in MEMORY:
        MEMORY[user_id] = []
    
    # Make sure it's a list before appending
    if not isinstance(MEMORY[user_id], list):
        MEMORY[user_id] = []
    
    MEMORY[user_id].append({
        "user": request.message,
        "assistant": response_text,
        "timestamp": time.time()
    })
    
    # Keep last 10
    if len(MEMORY[user_id]) > 10:
        MEMORY[user_id] = MEMORY[user_id][-10:]
    
    # Save
    try:
        with open("user_memory.json", 'w') as f:
            json.dump(MEMORY, f, indent=2)
        with open("relationship_profiles.json", 'w') as f:
            json.dump(PROFILES, f, indent=2)
    except Exception as e:
        print(f"Save error: {e}")
    
    # Response
    persona = "sarah" if user_gender == "male" else "xhash" if user_gender == "female" else "neutral"
    stage = "Close" if user_score >= 60 else "Friend" if user_score >= 30 else "Stranger"
    
    return {
        "response": response_text,
        "user_id": user_id,
        "memory_size": len(MEMORY.get(user_id, [])),
        "relationship": {
            "persona": persona,
            "stage": stage,
            "score": user_score
        },
        "stats": {
            "time": round(time.time() - start, 2),
            "context_used": bool(user_name)
        }
    }

@app.get("/health")
async def health():
    ahmed_info = "Not found"
    if "ahmed" in PROFILES:
        name = PROFILES["ahmed"].get("personal_info", {}).get("name")
        ahmed_info = f"Found (name={name})"
    
    return {
        "status": "healthy",
        "version": "clean_working",
        "profiles": len(PROFILES),
        "memories": len(MEMORY),
        "ahmed": ahmed_info
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
