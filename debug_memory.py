#!/usr/bin/env python3
"""
Debug version to see why memory isn't working
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
import time
import json
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

# Load model
print("Loading model...")
model = Llama(
    model_path="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
    n_ctx=1024,
    n_threads=4,
    n_batch=256,
    use_mmap=True,
    use_mlock=True,
    verbose=False
)
print("Model loaded!")

# Simple in-memory storage
memory_store = {}

class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"
    max_tokens: int = 150

@app.post("/api/test/memory")
async def test_memory(request: ChatRequest):
    """Test endpoint with simple memory"""
    
    # Initialize user memory if not exists
    if request.user_id not in memory_store:
        memory_store[request.user_id] = []
    
    # Build prompt with history
    prompt = ""
    
    # Add previous conversations
    if memory_store[request.user_id]:
        prompt += "Previous conversation:\n"
        for exchange in memory_store[request.user_id][-3:]:  # Last 3 exchanges
            prompt += f"User: {exchange['user']}\n"
            prompt += f"Assistant: {exchange['assistant']}\n"
        prompt += "\nContinue the conversation naturally, remembering what was discussed.\n\n"
    
    # Add current message
    prompt += f"User: {request.message}\nAssistant:"
    
    # DEBUG: Print the prompt
    print("\n" + "="*50)
    print("DEBUG PROMPT:")
    print(prompt)
    print("="*50)
    
    # Generate response
    response = model(
        prompt,
        max_tokens=request.max_tokens,
        temperature=0.7,
        stop=["User:", "\n\n"],
        echo=False
    )
    
    response_text = response['choices'][0]['text'].strip()
    
    # Store in memory
    memory_store[request.user_id].append({
        "user": request.message,
        "assistant": response_text,
        "timestamp": datetime.now().isoformat()
    })
    
    return {
        "response": response_text,
        "debug": {
            "user_id": request.user_id,
            "memory_count": len(memory_store[request.user_id]),
            "prompt_length": len(prompt),
            "history_included": len(memory_store[request.user_id]) > 1
        }
    }

@app.get("/api/test/memory/{user_id}")
async def get_memory(user_id: str):
    """Get memory for a user"""
    return {
        "user_id": user_id,
        "memory": memory_store.get(user_id, [])
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting debug server on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001)
