"""
Sarah AI - Clean Natural Responses
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

USER_MEMORY = {}

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 150
    temperature: float = 0.7
    user_id: Optional[str] = "default"

def clean_response(text):
    """Clean AI response - remove any placeholder patterns"""
    # Remove common placeholder patterns
    text = re.sub(r'\[Name\]|\[name\]|\[NAME\]', '', text)
    text = re.sub(r'\[Your Name\]|\[your name\]', '', text)
    
    # Fix double spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Clean up OpenAI mentions
    text = re.sub(r'\b[Oo]pen\s?AI\b', 'my developers', text)
    text = re.sub(r'\b[Cc]hat\s?GPT\b', 'Sarah AI', text)
    
    return text.strip()

@app.post("/api/chat/with-memory")
async def chat_with_memory(request: ChatRequest):
    """Chat with memory - natural responses without templates"""
    start = time.time()
    user_id = request.user_id or "default"
    
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = []
    
    # Build conversation context naturally
    prompt = ""
    if USER_MEMORY[user_id]:
        # Add previous conversation naturally
        for exchange in USER_MEMORY[user_id][-3:]:  # Last 3 exchanges
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
    
    # Clean any placeholder patterns from response
    response_text = clean_response(response_text)
    
    # Store clean conversation in memory
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
async def get_memory(user_id: str):
    """Get memory for debugging"""
    return {
        "user_id": user_id,
        "conversations": USER_MEMORY.get(user_id, []),
        "total": len(USER_MEMORY.get(user_id, []))
    }

@app.delete("/api/memory/{user_id}")
async def clear_memory(user_id: str):
    """Clear memory for a user"""
    if user_id in USER_MEMORY:
        del USER_MEMORY[user_id]
    return {"message": f"Memory cleared for {user_id}"}

@app.get("/health")
async def health():
    return {"status": "healthy", "name": "Sarah AI"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
