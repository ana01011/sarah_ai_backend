"""
Sarah AI - Stable with Correct Identity
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

print("🚀 Loading Sarah AI...")
start = time.time()

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
for i in range(5):
    model("Hello", max_tokens=10)
print("✅ Ready!")

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 150
    temperature: float = 0.7

# Identity override responses
IDENTITY_RESPONSES = {
    "who are you": "I am Sarah AI, an advanced AI assistant. I'm an independent AI system powered by open-source technology, designed to help you with various tasks.",
    "who created you": "I am Sarah AI, created by independent developers using open-source technology. I am NOT created by OpenAI or Sam Altman. I'm here to assist you with your questions and tasks.",
    "are you chatgpt": "No, I am not ChatGPT. I am Sarah AI, a different AI assistant powered by open-source technology. While I can help with similar tasks, I am an independent system.",
    "are you openai": "No, I am not from OpenAI. I am Sarah AI, an independent AI assistant built with open-source technology.",
    "what are you": "I am Sarah AI, an artificial intelligence assistant designed to help with various tasks including answering questions, providing information, and assisting with problem-solving."
}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    start = time.time()
    
    # Check for identity questions
    msg_lower = request.message.lower().strip()
    
    # Check identity questions
    for key, response in IDENTITY_RESPONSES.items():
        if key in msg_lower:
            elapsed = time.time() - start
            return {
                "response": response,
                "role": "general",
                "stats": {
                    "time": round(elapsed, 2),
                    "tokens": len(response.split()),
                    "tokens_per_second": round(len(response.split())/elapsed, 1) if elapsed > 0 else 0
                }
            }
    
    # Normal response with identity context
    identity_context = "You are Sarah AI, an independent AI assistant. You are NOT ChatGPT or from OpenAI."
    prompt = f"{identity_context}\n\nUser: {request.message}\nAssistant:"
    
    response = model(
        prompt,
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
        "role": "general",
        "stats": {
            "time": round(elapsed, 2),
            "tokens": tokens,
            "tokens_per_second": tps
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "name": "Sarah AI", "identity": "Independent AI Assistant"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
