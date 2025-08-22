"""
Sarah AI - With Persistent Memory
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
import time
import psutil
import re
from typing import Optional
from datetime import datetime
import json
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set CPU affinity
try:
    p = psutil.Process()
    p.cpu_affinity([4, 5, 6, 7])
except:
    pass

print("🚀 Loading Sarah AI...")
model = Llama(
    model_path="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
    n_ctx=1024,
    n_threads=4,
    n_batch=256,
    use_mmap=True,
    use_mlock=True,
    verbose=False
)
print("✅ Sarah AI Ready!")

# Memory storage file
MEMORY_FILE = "/root/openhermes_backend/user_memory.json"

def load_memory():
    """Load memory from file"""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_memory(memory):
    """Save memory to file"""
    try:
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory, f, indent=2)
    except Exception as e:
        print(f"Error saving memory: {e}")

# Load existing memory on startup
USER_MEMORY = load_memory()
print(f"📚 Loaded memory for {len(USER_MEMORY)} users")

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 150
    temperature: float = 0.7
    user_id: Optional[str] = "default"

def clean_response(text):
    """Clean AI response"""
    text = re.sub(r'\[Name\]|\[name\]|\[NAME\]', '', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\b[Oo]pen\s?AI\b', 'my developers', text)
    text = re.sub(r'\b[Cc]hat\s?GPT\b', 'Sarah AI', text)
    return text.strip()

def extract_important_info(message, response):
    """Extract important information to keep in permanent memory"""
    important = {}
    
    # Check for name introduction
    message_lower = message.lower()
    if 'my name is' in message_lower:
        parts = message_lower.split('my name is')
        if len(parts) > 1:
            name = parts[1].strip().split()[0]
            important['user_name'] = name.capitalize()
    
    # Check for other important personal info
    patterns = {
        'user_age': [r'i am (\d+)', r"i'm (\d+)", r'my age is (\d+)'],
        'user_location': [r'i live in ([\w\s]+)', r"i'm from ([\w\s]+)", r'my city is ([\w\s]+)'],
        'user_job': [r'i work as ([\w\s]+)', r"i'm a ([\w\s]+)", r'my job is ([\w\s]+)']
    }
    
    for key, patterns_list in patterns.items():
        for pattern in patterns_list:
            match = re.search(pattern, message_lower)
            if match:
                important[key] = match.group(1).strip()
                break
    
    return important

@app.post("/api/chat/with-memory")
async def chat_with_memory(request: ChatRequest):
    """Chat with persistent memory"""
    start = time.time()
    user_id = request.user_id or "default"
    
    # Initialize user memory if needed
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = {
            "conversations": [],
            "permanent_info": {},
            "created_at": datetime.now().isoformat()
        }
    
    user_data = USER_MEMORY[user_id]
    
    # Build context with permanent info first
    prompt = ""
    
    # Add permanent info to context
    if user_data.get("permanent_info"):
        info = user_data["permanent_info"]
        if info:
            context_parts = []
            if 'user_name' in info:
                context_parts.append(f"The user's name is {info['user_name']}")
            if 'user_age' in info:
                context_parts.append(f"They are {info['user_age']} years old")
            if 'user_location' in info:
                context_parts.append(f"They live in {info['user_location']}")
            if 'user_job' in info:
                context_parts.append(f"They work as {info['user_job']}")
            
            if context_parts:
                prompt = "Context: " + ". ".join(context_parts) + ".\n\n"
    
    # Add recent conversation history
    conversations = user_data.get("conversations", [])
    if conversations:
        # Include last 5 exchanges for context
        for exchange in conversations[-5:]:
            prompt += f"User: {exchange['user']}\n"
            prompt += f"Assistant: {exchange['assistant']}\n"
    
    # Add current message
    prompt += f"User: {request.message}\nAssistant:"
    
    # Generate response
    response = model(
        prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        stop=["User:", "\n\n"],
        echo=False
    )
    
    response_text = response['choices'][0]['text'].strip()
    response_text = clean_response(response_text)
    
    # Extract and store important information
    important_info = extract_important_info(request.message, response_text)
    if important_info:
        user_data["permanent_info"].update(important_info)
        print(f"📝 Stored permanent info for {user_id}: {important_info}")
    
    # Store conversation
    user_data["conversations"].append({
        "user": request.message,
        "assistant": response_text,
        "timestamp": datetime.now().isoformat()
    })
    
    # Keep only last 20 conversations (but permanent_info stays forever)
    if len(user_data["conversations"]) > 20:
        user_data["conversations"] = user_data["conversations"][-20:]
    
    # Save to disk periodically (every 5 messages)
    if len(user_data["conversations"]) % 5 == 0:
        save_memory(USER_MEMORY)
    
    elapsed = time.time() - start
    
    return {
        "response": response_text,
        "user_id": user_id,
        "memory_size": len(user_data["conversations"]),
        "has_name": "user_name" in user_data.get("permanent_info", {}),
        "stats": {
            "time": round(elapsed, 2),
            "context_used": True
        }
    }

@app.get("/api/memory/{user_id}")
async def get_memory(user_id: str):
    """Get memory for debugging"""
    if user_id in USER_MEMORY:
        return {
            "user_id": user_id,
            "permanent_info": USER_MEMORY[user_id].get("permanent_info", {}),
            "conversations": USER_MEMORY[user_id].get("conversations", []),
            "total": len(USER_MEMORY[user_id].get("conversations", []))
        }
    return {"user_id": user_id, "permanent_info": {}, "conversations": [], "total": 0}

@app.post("/api/memory/save")
async def force_save():
    """Force save memory to disk"""
    save_memory(USER_MEMORY)
    return {"message": f"Saved memory for {len(USER_MEMORY)} users"}

@app.get("/health")
async def health():
    return {"status": "healthy", "name": "Sarah AI", "users_in_memory": len(USER_MEMORY)}

# Save memory on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    save_memory(USER_MEMORY)
    print(f"💾 Saved memory for {len(USER_MEMORY)} users")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Auto-save memory every 60 seconds
import asyncio
import threading

def auto_save_memory():
    """Auto-save memory periodically"""
    while True:
        time.sleep(60)  # Save every minute
        if USER_MEMORY:
            save_memory(USER_MEMORY)
            print(f"⏰ Auto-saved memory for {len(USER_MEMORY)} users")

# Start auto-save thread
save_thread = threading.Thread(target=auto_save_memory, daemon=True)
save_thread.start()
print("💾 Auto-save enabled (every 60 seconds)")

# ============= CROSS-DEVICE SYNC =============
from fastapi import Request

@app.post("/api/chat/with-memory-sync")
async def chat_with_sync(request: ChatRequest, req: Request):
    """Chat with memory that syncs across devices using IP"""
    # Use IP address as base for user ID if not provided
    client_ip = req.client.host
    
    # Create a consistent user ID based on IP
    if not request.user_id or request.user_id.startswith('user_'):
        request.user_id = f"ip_{client_ip.replace('.', '_')}"
    
    # Use the regular chat function with the IP-based ID
    return await chat_with_memory(request)

@app.get("/api/sync/code")
async def get_sync_code(req: Request):
    """Generate a sync code for current user"""
    client_ip = req.client.host
    user_id = f"ip_{client_ip.replace('.', '_')}"
    
    # Simple code generation
    import hashlib
    code = hashlib.md5(user_id.encode()).hexdigest()[:6].upper()
    
    return {"code": code, "user_id": user_id}
# ============= END CROSS-DEVICE SYNC =============

# ============= REQUEST LOGGING =============
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for debugging"""
    if request.url.path == "/api/chat/with-memory":
        body = await request.body()
        print(f"Request from {request.client.host}:")
        print(f"User-Agent: {request.headers.get('user-agent', 'Unknown')}")
        print(f"Body: {body.decode('utf-8')}")
        
        # Recreate request with body
        import io
        request._body = body
        request.stream = lambda: io.BytesIO(body)
    
    response = await call_next(request)
    return response
# ============= END REQUEST LOGGING =============

@app.post("/api/test/device")
async def test_device(request: ChatRequest, req: Request):
    """Test endpoint to debug device differences"""
    user_agent = req.headers.get('user-agent', 'Unknown')
    is_mobile = any(device in user_agent.lower() for device in ['android', 'iphone', 'mobile'])
    
    return {
        "device": "mobile" if is_mobile else "desktop",
        "user_id": request.user_id,
        "message": request.message,
        "memory_size": len(USER_MEMORY.get(request.user_id, [])),
        "user_agent": user_agent[:100]
    }
