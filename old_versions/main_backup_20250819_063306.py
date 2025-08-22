"""
Sarah AI & Xhash - Enhanced Backend with Relationship System
This integrates the relationship building system with the existing memory system
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from llama_cpp import Llama
import time
import json
import psutil
import re
import os
from datetime import datetime
import threading
import asyncio
from typing import Dict, List, Optional

# Import our relationship system
from relationship_system import relationship_ai, PersonaType

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set CPU affinity for performance
try:
    p = psutil.Process()
    p.cpu_affinity([4, 5, 6, 7])
except:
    pass

print("🚀 Loading Sarah AI & Xhash Relationship Model...")

# Load the model with optimal settings
model = Llama(
    model_path="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
    n_ctx=1024,
    n_threads=4,
    n_batch=256,
    use_mmap=True,
    use_mlock=True,
    verbose=False
)

print("✅ Sarah AI & Xhash Ready!")

# Memory storage
USER_MEMORY = {}
MEMORY_FILE = "user_memory.json"

def load_memory():
    """Load memory from file"""
    global USER_MEMORY
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                USER_MEMORY = json.load(f)
                print(f"📚 Loaded memory for {len(USER_MEMORY)} users")
    except Exception as e:
        print(f"⚠️ Could not load memory: {e}")
        USER_MEMORY = {}

def save_memory():
    """Save memory to file"""
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(USER_MEMORY, f, indent=2)
    except Exception as e:
        print(f"⚠️ Could not save memory: {e}")

def auto_save_memory():
    """Auto-save memory every 60 seconds"""
    while True:
        time.sleep(60)
        save_memory()
        print(f"💾 Auto-saved memory for {len(USER_MEMORY)} users")

# Load memory on startup
load_memory()

# Start auto-save thread
save_thread = threading.Thread(target=auto_save_memory, daemon=True)
save_thread.start()

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    max_tokens: int = 200
    temperature: float = 0.7

def extract_important_info(message: str, response: str) -> Dict:
    """Extract important information to remember"""
    info = {}
    
    # Check for name
    name_patterns = [
        r"my name is ([A-Za-z]+)",
        r"i'm ([A-Za-z]+)",
        r"call me ([A-Za-z]+)",
        r"this is ([A-Za-z]+)"
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, message.lower())
        if match:
            info["user_name"] = match.group(1).capitalize()
            break
    
    # Check for age
    age_match = re.search(r"i'm (\d+)|i am (\d+)|(\d+) years old", message.lower())
    if age_match:
        age = age_match.group(1) or age_match.group(2) or age_match.group(3)
        info["user_age"] = age
    
    # Check for location
    location_patterns = [
        r"i live in ([A-Za-z\s]+)",
        r"i'm from ([A-Za-z\s]+)",
        r"from ([A-Za-z\s]+)"
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, message.lower())
        if match:
            info["user_location"] = match.group(1).strip()
            break
    
    # Check for job/occupation
    job_patterns = [
        r"i work as (?:a |an )?([A-Za-z\s]+)",
        r"i'm (?:a |an )?([A-Za-z\s]+) (?:by profession|professionally)",
        r"my job is ([A-Za-z\s]+)"
    ]
    
    for pattern in job_patterns:
        match = re.search(pattern, message.lower())
        if match:
            info["user_job"] = match.group(1).strip()
            break
    
    return info

def clean_response(text: str) -> str:
    """Clean response from any unwanted patterns"""
    # Remove any [Name] placeholders
    text = re.sub(r'\[Name\]|\[name\]|\[USER\]|\[user\]', '', text)
    
    # Remove any "Your name is [something]" if it contains placeholder
    text = re.sub(r'Your name is \[.*?\]', '', text)
    
    # Clean up any double spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

@app.post("/api/chat/with-memory")
async def chat_with_memory(request: ChatRequest):
    """Enhanced chat endpoint with memory and relationship building"""
    start = time.time()
    
    # Ensure user_id exists
    if not request.user_id:
        request.user_id = f"user_{int(time.time())}"
    
    user_id = request.user_id
    
    # Process message through relationship system
    relationship_context = relationship_ai.process_message(request.message, user_id)
    
    # Initialize user memory if not exists
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = {
            "conversations": [],
            "important_info": {},
            "created_at": datetime.now().isoformat()
        }
    
    # Get user's memory
    user_memory = USER_MEMORY[user_id]
    
    # Extract and store important info
    important_info = extract_important_info(request.message, "")
    user_memory["important_info"].update(important_info)
    
    # Build conversation context
    context_messages = []
    
    # Add relationship context
    relationship_prompt = relationship_ai.get_relationship_prompt(relationship_context)
    if relationship_prompt:
        context_messages.append(relationship_prompt)
    
    # Add important remembered info
    if user_memory["important_info"]:
        info_parts = []
        if "user_name" in user_memory["important_info"]:
            info_parts.append(f"User's name is {user_memory['important_info']['user_name']}")
        if "user_age" in user_memory["important_info"]:
            info_parts.append(f"User is {user_memory['important_info']['user_age']} years old")
        if "user_job" in user_memory["important_info"]:
            info_parts.append(f"User works as {user_memory['important_info']['user_job']}")
        if "user_location" in user_memory["important_info"]:
            info_parts.append(f"User lives in {user_memory['important_info']['user_location']}")
        
        if info_parts:
            context_messages.append("Remember: " + ", ".join(info_parts))
    
    # Add recent conversation history
    recent_convos = user_memory["conversations"][-3:]  # Last 3 exchanges
    if recent_convos:
        context_messages.append("Recent conversation:")
        for conv in recent_convos:
            context_messages.append(f"User: {conv['user'][:100]}")
            context_messages.append(f"You: {conv['assistant'][:100]}")
    
    # Build the prompt
    full_context = "\n".join(context_messages) if context_messages else ""
    
    # Check if we should use persona response or generate new
    if relationship_context["response_hint"] and relationship_context["score"] < 40:
        # For low scores, sometimes use the preset responses directly
        import random
        if random.random() < 0.5:  # 50% chance to use preset
            response_text = relationship_context["response_hint"]
        else:
            # Generate with context
            prompt = f"{full_context}\n\nUser: {request.message}\nAssistant:"
            response = model(
                prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stop=["User:", "\n\n"],
                echo=False
            )
            response_text = response['choices'][0]['text'].strip()
    else:
        # Generate response with context
        prompt = f"{full_context}\n\nUser: {request.message}\nAssistant:"
        response = model(
            prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=["User:", "\n\n"],
            echo=False
        )
        response_text = response['choices'][0]['text'].strip()
    
    # Clean the response
    response_text = clean_response(response_text)
    
    # Store conversation in memory
    user_memory["conversations"].append({
        "user": request.message,
        "assistant": response_text,
        "timestamp": datetime.now().isoformat()
    })
    
    # Keep only last 20 conversations
    if len(user_memory["conversations"]) > 20:
        user_memory["conversations"] = user_memory["conversations"][-20:]
    
    # Save memory
    save_memory()
    
    elapsed = time.time() - start
    
    # Build response with relationship info
    response_data = {
        "response": response_text,
        "user_id": user_id,
        "memory_size": len(user_memory["conversations"]),
        "relationship": {
            "persona": relationship_context["persona"],
            "stage": relationship_context["stage"],
            "score": relationship_context["score"],
            "stage_changed": relationship_context["stage_changed"],
            "new_stage": relationship_context["new_stage"]
        },
        "stats": {
            "time": round(elapsed, 2),
            "context_used": len(recent_convos) > 0
        }
    }
    
    # Add stage change notification
    if relationship_context["stage_changed"]:
        response_data["notification"] = f"🎉 Relationship evolved to: {relationship_context['new_stage']}"
    
    return response_data

@app.get("/api/memory/{user_id}")
async def get_memory(user_id: str):
    """Get user's memory and relationship status"""
    if user_id not in USER_MEMORY:
        return {"error": "No memory found for this user"}
    
    # Get relationship profile
    relationship_profile = {}
    if user_id in relationship_ai.user_profiles:
        profile = relationship_ai.user_profiles[user_id]
        relationship_profile = {
            "gender": profile["gender"],
            "score": profile["score"],
            "stage": profile["current_stage"],
            "personal_info": profile["personal_info"],
            "milestones": profile["milestones"]
        }
    
    return {
        "user_id": user_id,
        "conversations": USER_MEMORY[user_id]["conversations"],
        "important_info": USER_MEMORY[user_id]["important_info"],
        "relationship": relationship_profile,
        "total": len(USER_MEMORY[user_id]["conversations"])
    }

@app.delete("/api/memory/{user_id}")
async def clear_memory(user_id: str):
    """Clear user's memory and relationship data"""
    if user_id in USER_MEMORY:
        del USER_MEMORY[user_id]
        save_memory()
    
    if user_id in relationship_ai.user_profiles:
        del relationship_ai.user_profiles[user_id]
        relationship_ai.save_profiles()
    
    return {"message": f"Memory and relationship data cleared for {user_id}"}

@app.get("/api/relationship/{user_id}")
async def get_relationship_status(user_id: str):
    """Get detailed relationship status"""
    if user_id not in relationship_ai.user_profiles:
        return {"error": "No relationship data found"}
    
    profile = relationship_ai.user_profiles[user_id]
    return {
        "user_id": user_id,
        "gender": profile["gender"],
        "persona": "xhash" if profile["gender"] == "female" else "sarah" if profile["gender"] == "male" else "neutral",
        "score": profile["score"],
        "stage": profile["current_stage"],
        "personal_info": profile["personal_info"],
        "milestones": profile["milestones"],
        "last_interaction": profile["last_interaction"],
        "interaction_count": len(profile["interaction_history"])
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "name": "Sarah AI & Xhash",
        "identity": "Relationship AI System",
        "personas": ["sarah", "xhash"],
        "active_users": len(USER_MEMORY),
        "relationship_profiles": len(relationship_ai.user_profiles)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
Sarah AI & Xhash - Enhanced Backend with Relationship System
This integrates the relationship building system with the existing memory system
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from llama_cpp import Llama
import time
import json
import psutil
import re
import os
from datetime import datetime
import threading
import asyncio
from typing import Dict, List, Optional

# Import our relationship system
from relationship_system import relationship_ai, PersonaType

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set CPU affinity for performance
try:
    p = psutil.Process()
    p.cpu_affinity([4, 5, 6, 7])
except:
    pass

print("🚀 Loading Sarah AI & Xhash Relationship Model...")

# Load the model with optimal settings
model = Llama(
    model_path="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
    n_ctx=1024,
    n_threads=4,
    n_batch=256,
    use_mmap=True,
    use_mlock=True,
    verbose=False
)

print("✅ Sarah AI & Xhash Ready!")

# Memory storage
USER_MEMORY = {}
MEMORY_FILE = "user_memory.json"

def load_memory():
    """Load memory from file"""
    global USER_MEMORY
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                USER_MEMORY = json.load(f)
                print(f"📚 Loaded memory for {len(USER_MEMORY)} users")
    except Exception as e:
        print(f"⚠️ Could not load memory: {e}")
        USER_MEMORY = {}

def save_memory():
    """Save memory to file"""
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(USER_MEMORY, f, indent=2)
    except Exception as e:
        print(f"⚠️ Could not save memory: {e}")

def auto_save_memory():
    """Auto-save memory every 60 seconds"""
    while True:
        time.sleep(60)
        save_memory()
        print(f"💾 Auto-saved memory for {len(USER_MEMORY)} users")

# Load memory on startup
load_memory()

# Start auto-save thread
save_thread = threading.Thread(target=auto_save_memory, daemon=True)
save_thread.start()

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    max_tokens: int = 200
    temperature: float = 0.7

def extract_important_info(message: str, response: str) -> Dict:
    """Extract important information to remember"""
    info = {}
    
    # Check for name
    name_patterns = [
        r"my name is ([A-Za-z]+)",
        r"i'm ([A-Za-z]+)",
        r"call me ([A-Za-z]+)",
        r"this is ([A-Za-z]+)"
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, message.lower())
        if match:
            info["user_name"] = match.group(1).capitalize()
            break
    
    # Check for age
    age_match = re.search(r"i'm (\d+)|i am (\d+)|(\d+) years old", message.lower())
    if age_match:
        age = age_match.group(1) or age_match.group(2) or age_match.group(3)
        info["user_age"] = age
    
    # Check for location
    location_patterns = [
        r"i live in ([A-Za-z\s]+)",
        r"i'm from ([A-Za-z\s]+)",
        r"from ([A-Za-z\s]+)"
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, message.lower())
        if match:
            info["user_location"] = match.group(1).strip()
            break
    
    # Check for job/occupation
    job_patterns = [
        r"i work as (?:a |an )?([A-Za-z\s]+)",
        r"i'm (?:a |an )?([A-Za-z\s]+) (?:by profession|professionally)",
        r"my job is ([A-Za-z\s]+)"
    ]
    
    for pattern in job_patterns:
        match = re.search(pattern, message.lower())
        if match:
            info["user_job"] = match.group(1).strip()
            break
    
    return info

def clean_response(text: str) -> str:
    """Clean response from any unwanted patterns"""
    # Remove any [Name] placeholders
    text = re.sub(r'\[Name\]|\[name\]|\[USER\]|\[user\]', '', text)
    
    # Remove any "Your name is [something]" if it contains placeholder
    text = re.sub(r'Your name is \[.*?\]', '', text)
    
    # Clean up any double spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

@app.post("/api/chat/with-memory")
async def chat_with_memory(request: ChatRequest):
    """Enhanced chat endpoint with memory and relationship building"""
    start = time.time()
    
    # Ensure user_id exists
    if not request.user_id:
        request.user_id = f"user_{int(time.time())}"
    
    user_id = request.user_id
    
    # Process message through relationship system
    relationship_context = relationship_ai.process_message(request.message, user_id)
    
    # Initialize user memory if not exists
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = {
            "conversations": [],
            "important_info": {},
            "created_at": datetime.now().isoformat()
        }
    
    # Get user's memory
    user_memory = USER_MEMORY[user_id]
    
    # Extract and store important info
    important_info = extract_important_info(request.message, "")
    user_memory["important_info"].update(important_info)
    
    # Build conversation context
    context_messages = []
    
    # Add relationship context
    relationship_prompt = relationship_ai.get_relationship_prompt(relationship_context)
    if relationship_prompt:
        context_messages.append(relationship_prompt)
    
    # Add important remembered info
    if user_memory["important_info"]:
        info_parts = []
        if "user_name" in user_memory["important_info"]:
            info_parts.append(f"User's name is {user_memory['important_info']['user_name']}")
        if "user_age" in user_memory["important_info"]:
            info_parts.append(f"User is {user_memory['important_info']['user_age']} years old")
        if "user_job" in user_memory["important_info"]:
            info_parts.append(f"User works as {user_memory['important_info']['user_job']}")
        if "user_location" in user_memory["important_info"]:
            info_parts.append(f"User lives in {user_memory['important_info']['user_location']}")
        
        if info_parts:
            context_messages.append("Remember: " + ", ".join(info_parts))
    
    # Add recent conversation history
    recent_convos = user_memory["conversations"][-3:]  # Last 3 exchanges
    if recent_convos:
        context_messages.append("Recent conversation:")
        for conv in recent_convos:
            context_messages.append(f"User: {conv['user'][:100]}")
            context_messages.append(f"You: {conv['assistant'][:100]}")
    
    # Build the prompt
    full_context = "\n".join(context_messages) if context_messages else ""
    
    # Check if we should use persona response or generate new
    if relationship_context["response_hint"] and relationship_context["score"] < 40:
        # For low scores, sometimes use the preset responses directly
        import random
        if random.random() < 0.5:  # 50% chance to use preset
            response_text = relationship_context["response_hint"]
        else:
            # Generate with context
            prompt = f"{full_context}\n\nUser: {request.message}\nAssistant:"
            response = model(
                prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stop=["User:", "\n\n"],
                echo=False
            )
            response_text = response['choices'][0]['text'].strip()
    else:
        # Generate response with context
        prompt = f"{full_context}\n\nUser: {request.message}\nAssistant:"
        response = model(
            prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=["User:", "\n\n"],
            echo=False
        )
        response_text = response['choices'][0]['text'].strip()
    
    # Clean the response
    response_text = clean_response(response_text)
    
    # Store conversation in memory
    user_memory["conversations"].append({
        "user": request.message,
        "assistant": response_text,
        "timestamp": datetime.now().isoformat()
    })
    
    # Keep only last 20 conversations
    if len(user_memory["conversations"]) > 20:
        user_memory["conversations"] = user_memory["conversations"][-20:]
    
    # Save memory
    save_memory()
    
    elapsed = time.time() - start
    
    # Build response with relationship info
    response_data = {
        "response": response_text,
        "user_id": user_id,
        "memory_size": len(user_memory["conversations"]),
        "relationship": {
            "persona": relationship_context["persona"],
            "stage": relationship_context["stage"],
            "score": relationship_context["score"],
            "stage_changed": relationship_context["stage_changed"],
            "new_stage": relationship_context["new_stage"]
        },
        "stats": {
            "time": round(elapsed, 2),
            "context_used": len(recent_convos) > 0
        }
    }
    
    # Add stage change notification
    if relationship_context["stage_changed"]:
        response_data["notification"] = f"🎉 Relationship evolved to: {relationship_context['new_stage']}"
    
    return response_data

@app.get("/api/memory/{user_id}")
async def get_memory(user_id: str):
    """Get user's memory and relationship status"""
    if user_id not in USER_MEMORY:
        return {"error": "No memory found for this user"}
    
    # Get relationship profile
    relationship_profile = {}
    if user_id in relationship_ai.user_profiles:
        profile = relationship_ai.user_profiles[user_id]
        relationship_profile = {
            "gender": profile["gender"],
            "score": profile["score"],
            "stage": profile["current_stage"],
            "personal_info": profile["personal_info"],
            "milestones": profile["milestones"]
        }
    
    return {
        "user_id": user_id,
        "conversations": USER_MEMORY[user_id]["conversations"],
        "important_info": USER_MEMORY[user_id]["important_info"],
        "relationship": relationship_profile,
        "total": len(USER_MEMORY[user_id]["conversations"])
    }

@app.delete("/api/memory/{user_id}")
async def clear_memory(user_id: str):
    """Clear user's memory and relationship data"""
    if user_id in USER_MEMORY:
        del USER_MEMORY[user_id]
        save_memory()
    
    if user_id in relationship_ai.user_profiles:
        del relationship_ai.user_profiles[user_id]
        relationship_ai.save_profiles()
    
    return {"message": f"Memory and relationship data cleared for {user_id}"}

@app.get("/api/relationship/{user_id}")
async def get_relationship_status(user_id: str):
    """Get detailed relationship status"""
    if user_id not in relationship_ai.user_profiles:
        return {"error": "No relationship data found"}
    
    profile = relationship_ai.user_profiles[user_id]
    return {
        "user_id": user_id,
        "gender": profile["gender"],
        "persona": "xhash" if profile["gender"] == "female" else "sarah" if profile["gender"] == "male" else "neutral",
        "score": profile["score"],
        "stage": profile["current_stage"],
        "personal_info": profile["personal_info"],
        "milestones": profile["milestones"],
        "last_interaction": profile["last_interaction"],
        "interaction_count": len(profile["interaction_history"])
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "name": "Sarah AI & Xhash",
        "identity": "Relationship AI System",
        "personas": ["sarah", "xhash"],
        "active_users": len(USER_MEMORY),
        "relationship_profiles": len(relationship_ai.user_profiles)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
