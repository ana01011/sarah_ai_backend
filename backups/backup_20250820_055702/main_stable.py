"""
Sarah AI - Stable Working Configuration
Proven 16-18 tok/s performance
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
import time
import psutil

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
    print("✅ Using cores 4-7")
except:
    print("⚠️ Could not set CPU affinity")

print("🚀 Loading OpenHermes...")
start = time.time()

# PROVEN WORKING CONFIGURATION - DON'T CHANGE
model = Llama(
    model_path="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
    n_ctx=1024,  # Keep this
    n_threads=4,  # Keep this
    n_threads_batch=4,
    n_batch=256,  # Keep this
    seed=42,
    use_mmap=True,
    use_mlock=True,
    f16_kv=True,
    verbose=False
)

print(f"✅ Model loaded in {time.time()-start:.1f}s")

# Simple warmup that works
print("🔥 Warming up...")
for i in range(5):
    model("Hello", max_tokens=10)
print("✅ Ready!")

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 150
    temperature: float = 0.7

@app.post("/api/chat")
async def chat(request: ChatRequest):
    start = time.time()
    
    response = model(
        f"User: {request.message}\nAssistant:",
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
    tps = round(tokens/elapsed, 1)
    
    print(f"⚡ {tokens} tokens in {elapsed:.1f}s = {tps} tok/s")
    
    return {
        "response": text,
        "stats": {
            "time": round(elapsed, 2),
            "tokens": tokens,
            "tokens_per_second": tps
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
