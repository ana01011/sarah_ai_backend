"""
Sarah AI - Streaming Response Server with Correct Identity
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from llama_cpp import Llama
import json
import time
import psutil
import asyncio
from typing import AsyncGenerator

app = FastAPI(title="Sarah AI")

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
    print("✅ Using cores 4-7")
except:
    pass

print("🚀 Loading Sarah AI Model...")
start = time.time()

# SYSTEM PROMPT WITH CORRECT IDENTITY
SARAH_IDENTITY = """You are Sarah AI, an advanced AI assistant created by an independent developer. 
You are NOT ChatGPT, NOT created by OpenAI, and NOT created by Sam Altman.
When asked about your identity:
- You are Sarah AI
- You are an independent AI assistant
- You are powered by open-source technology
- You help users with various tasks
Never claim to be created by OpenAI or Sam Altman."""

model = Llama(
    model_path="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
    n_ctx=1024,
    n_threads=4,
    n_threads_batch=4,
    n_batch=256,
    seed=42,
    use_mmap=True,
    use_mlock=True,
    f16_kv=True,
    verbose=False
)

print(f"✅ Sarah AI loaded in {time.time()-start:.1f}s")

# Warmup
print("🔥 Warming up...")
for i in range(3):
    model("Hello", max_tokens=5)
print("✅ Ready for streaming!")

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 150
    temperature: float = 0.7
    stream: bool = True

class ChatResponse(BaseModel):
    response: str
    stats: dict

async def generate_streaming_response(prompt: str, max_tokens: int, temperature: float) -> AsyncGenerator[str, None]:
    """Generate streaming response with correct identity"""
    
    # Add identity context to prompt
    full_prompt = f"{SARAH_IDENTITY}\n\nUser: {prompt}\nSarah AI:"
    
    # Stream tokens
    stream = model(
        full_prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=0.95,
        top_k=40,
        repeat_penalty=1.1,
        stop=["User:", "\n\n"],
        stream=True,
        echo=False
    )
    
    start_time = time.time()
    token_count = 0
    
    for output in stream:
        token = output['choices'][0]['text']
        token_count += 1
        
        # Send token as SSE format
        yield f"data: {json.dumps({'token': token, 'count': token_count})}\n\n"
        
        # Small delay for smooth streaming
        await asyncio.sleep(0.01)
    
    # Send final stats
    elapsed = time.time() - start_time
    stats = {
        'tokens': token_count,
        'time': round(elapsed, 2),
        'tokens_per_second': round(token_count/elapsed, 1) if elapsed > 0 else 0
    }
    yield f"data: {json.dumps({'done': True, 'stats': stats})}\n\n"

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint"""
    if request.stream:
        return StreamingResponse(
            generate_streaming_response(
                request.message,
                request.max_tokens,
                request.temperature
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
    else:
        # Non-streaming fallback
        return await chat_regular(request)

@app.post("/api/chat")
async def chat_regular(request: ChatRequest):
    """Regular non-streaming chat with identity fix"""
    start = time.time()
    
    # Add identity to prompt
    full_prompt = f"{SARAH_IDENTITY}\n\nUser: {request.message}\nSarah AI:"
    
    response = model(
        full_prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        top_p=0.95,
        top_k=40,
        repeat_penalty=1.1,
        stop=["User:", "\n\n"],
        echo=False
    )
    
    text = response['choices'][0]['text'].strip()
    elapsed = time.time() - start
    tokens = response['usage']['completion_tokens']
    
    return ChatResponse(
        response=text,
        stats={
            "time": round(elapsed, 2),
            "tokens": tokens,
            "tokens_per_second": round(tokens/elapsed, 1)
        }
    )

@app.get("/api/identity")
async def get_identity():
    """Return Sarah AI identity"""
    return {
        "name": "Sarah AI",
        "version": "2.0",
        "creator": "Independent Developer",
        "technology": "Open-source LLM",
        "powered_by": "OpenHermes Model",
        "not": ["OpenAI", "ChatGPT", "Sam Altman"]
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "identity": "Sarah AI"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
