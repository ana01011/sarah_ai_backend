"""
OpenHermes - Fixed Performance Version
Solves alternating speed issue
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
import time
import os
import gc

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Disable Python garbage collection during inference
gc.disable()

print("🚀 Loading OpenHermes (Performance Fixed)...")
start = time.time()

# FIXED CONFIGURATION
model = Llama(
    model_path="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
    n_ctx=1024,
    n_threads=2,  # Use only 2 threads to avoid contention
    n_batch=128,  # Smaller batch
    seed=42,  # Fixed seed for consistency
    use_mmap=True,
    use_mlock=True,
    verbose=False
)

print(f"✅ Loaded in {time.time()-start:.1f}s")

# Warm up multiple times
print("🔥 Warming up...")
for _ in range(3):
    model("Hello", max_tokens=5, temperature=0.1)
print("⚡ Ready!")

# Re-enable GC
gc.enable()

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 100

# Track request count
request_count = 0

@app.post("/api/chat")
async def chat(request: ChatRequest):
    global request_count
    request_count += 1
    
    # Force GC before every request to be consistent
    gc.collect()
    
    start = time.time()
    
    # Add request number to track pattern
    print(f"\n📝 Request #{request_count}")
    
    response = model(
        f"User: {request.message}\nAssistant:",
        max_tokens=request.max_tokens,
        temperature=0.7,
        top_p=0.95,
        stop=["User:", "\n\n"],
        echo=False
    )
    
    text = response['choices'][0]['text'].strip()
    elapsed = time.time() - start
    tokens = response['usage']['completion_tokens']
    tps = round(tokens/elapsed, 1)
    
    print(f"⚡ Request #{request_count}: {tokens} tokens in {elapsed:.1f}s = {tps} tok/s")
    
    return {
        "response": text,
        "request_num": request_count,
        "stats": {
            "time": round(elapsed, 2),
            "tokens": tokens,
            "tokens_per_second": tps
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "requests_served": request_count}

if __name__ == "__main__":
    import uvicorn
    # Single worker to avoid process switching
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1, loop="asyncio")
