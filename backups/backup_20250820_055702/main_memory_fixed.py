"""
Sarah AI - With Working Memory System
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
import time
import psutil
import re
from typing import Optional, Dict, List
from datetime import datetime
import json

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

# Simple but effective memory system
USER_MEMORY = {}

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 150
    temperature: float = 0.7
    user_id: Optional[str] = "default"

def is_identity_question(message):
    """Check if asking about identity/creator"""
    msg = message.lower()
    identity_words = [
        'who created', 'who made', 'who built', 'who designed',
        'who developed', 'who are you', 'what are you',
        'created by', 'made by', 'built by', 'designed by',
        'your creator', 'your developer', 'your maker',
        'openai', 'open ai', 'chatgpt', 'gpt', 'anthropic', 'claude'
    ]
    return any(word in msg for word in identity_words)

def clean_response(text):
    """Remove ALL mentions of other AIs and companies"""
    replacements = {
        r'\b[Oo]pen\s?AI\b': 'my developers',
        r'\b[Cc]hat\s?GPT\b': 'Sarah AI',
        r'\b[Gg]PT[-\s]?\d*\b': 'Sarah AI',
        r'\b[Aa]nthrop[ic]*\b': 'my developers',
        r'\b[Cc]laude\b': 'Sarah AI',
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)
    
    problem_words = ['openai', 'open ai', 'chatgpt', 'gpt-', 'anthropic', 'claude']
    if any(word in text.lower() for word in problem_words):
        return "I'm Sarah AI, an independent AI assistant. How can I help you?"
    
    return text

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Original chat endpoint"""
    start = time.time()
    
    if is_identity_question(request.message):
        response_text = "I'm Sarah AI, an independent AI assistant created by independent developers using open-source technology."
    else:
        response = model(
            f"User: {request.message}\nAssistant:",
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=["User:"],
            echo=False
        )
        response_text = response['choices'][0]['text'].strip()
        response_text = clean_response(response_text)
    
    elapsed = time.time() - start
    return {
        "response": response_text,
        "role": "general",
        "stats": {
            "time": round(elapsed, 2),
            "tokens": len(response_text.split()),
            "tokens_per_second": round(len(response_text.split())/elapsed, 1)
        }
    }

@app.post("/api/chat/with-memory")
async def chat_with_memory(request: ChatRequest):
    """Chat with working memory"""
    start = time.time()
    user_id = request.user_id or "default"
    
    # Initialize user memory if needed
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = []
    
    # Check for identity question
    if is_identity_question(request.message):
        response_text = "I'm Sarah AI, an independent AI assistant created by independent developers."
    else:
        # Build context-aware prompt
        prompt = ""
        
        # Add conversation history
        if USER_MEMORY[user_id]:
            prompt = "You are Sarah AI. Remember this conversation:\n\n"
            for exchange in USER_MEMORY[user_id][-3:]:  # Last 3 exchanges
                prompt += f"User: {exchange['user']}\n"
                prompt += f"Sarah: {exchange['assistant']}\n"
            prompt += "\nBased on the above conversation, respond to:\n"
        
        prompt += f"User: {request.message}\nSarah:"
        
        # Generate response with context
        response = model(
            prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=["User:", "\n\n"],
            echo=False
        )
        response_text = response['choices'][0]['text'].strip()
        response_text = clean_response(response_text)
    
    # Store in memory
    USER_MEMORY[user_id].append({
        "user": request.message,
        "assistant": response_text,
        "timestamp": datetime.now().isoformat()
    })
    
    # Keep only last 10 exchanges
    if len(USER_MEMORY[user_id]) > 10:
        USER_MEMORY[user_id] = USER_MEMORY[user_id][-10:]
    
    elapsed = time.time() - start
    
    return {
        "response": response_text,
        "user_id": user_id,
        "memory_size": len(USER_MEMORY[user_id]),
        "stats": {
            "time": round(elapsed, 2),
            "context_used": len(USER_MEMORY[user_id]) > 1
        }
    }

@app.get("/api/memory/{user_id}")
async def get_user_memory(user_id: str):
    """Get memory for a specific user"""
    return {
        "user_id": user_id,
        "conversations": USER_MEMORY.get(user_id, []),
        "total": len(USER_MEMORY.get(user_id, []))
    }

@app.delete("/api/memory/{user_id}")
async def clear_user_memory(user_id: str):
    """Clear memory for a specific user"""
    if user_id in USER_MEMORY:
        del USER_MEMORY[user_id]
    return {"message": f"Memory cleared for {user_id}"}

@app.get("/health")
async def health():
    return {"status": "healthy", "name": "Sarah AI", "memory_users": len(USER_MEMORY)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
