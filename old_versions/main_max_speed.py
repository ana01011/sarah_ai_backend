"""
OpenHermes - Maximum Speed with CPU Isolation
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
import time
import os
import psutil

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set CPU affinity to cores 2-7 (leaving 0-1 for system)
try:
    p = psutil.Process()
    p.cpu_affinity([2, 3, 4, 5, 6, 7])  # Use cores 2-7
    print(f"🔒 CPU affinity set to cores: {p.cpu_affinity()}")
except:
    print("⚠️ Could not set CPU affinity")

print("⚡ Loading OpenHermes MAX SPEED...")
start = time.time()

# MAX SPEED CONFIGURATION
model = Llama(
    model_path="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
    n_ctx=512,  # Small context for speed
    n_threads=6,  # Use 6 dedicated cores
    n_threads_batch=6,
    n_batch=512,  # Maximum batch
    seed=42,
    use_mmap=True,
    use_mlock=True,
    f16_kv=True,
    mul_mat_q=True,
    logits_all=False,
    verbose=False
)

print(f"✅ Loaded in {time.time()-start:.1f}s")

# Extensive warmup
print("🔥 Warming up on dedicated cores...")
for i in range(10):
    model(f"Warmup {i}", max_tokens=20, temperature=0.1)
print("🚀 MAX SPEED mode ready!")

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 100

request_count = 0
speeds = []

@app.post("/api/chat")
async def chat(request: ChatRequest):
    global request_count, speeds
    request_count += 1
    
    start = time.time()
    
    response = model(
        f"User: {request.message}\nAssistant:",
        max_tokens=request.max_tokens,
        temperature=0.7,
        top_p=0.9,  # Tighter top_p for speed
        top_k=30,   # Smaller top_k for speed
        repeat_penalty=1.1,
        stop=["User:", "\n\n"],
        echo=False
    )
    
    elapsed = time.time() - start
    tokens = response['usage']['completion_tokens']
    tps = round(tokens/elapsed, 1)
    speeds.append(tps)
    
    # Calculate rolling average of last 5 requests
    recent_speeds = speeds[-5:] if len(speeds) >= 5 else speeds
    avg_speed = round(sum(recent_speeds)/len(recent_speeds), 1)
    
    print(f"🚀 Request #{request_count}: {tokens} tok in {elapsed:.1f}s = {tps} tok/s (Avg: {avg_speed})")
    
    return {
        "response": response['choices'][0]['text'].strip(),
        "stats": {
            "time": round(elapsed, 2),
            "tokens": tokens,
            "tokens_per_second": tps,
            "avg_speed": avg_speed
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
