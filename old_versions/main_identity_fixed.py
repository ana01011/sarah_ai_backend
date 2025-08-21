"""
Sarah AI - With FORCED Identity Override
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
import time
import psutil
import re

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
    pass

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
for i in range(5):
    model("Hello", max_tokens=10)
print("✅ Ready!")

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 150
    temperature: float = 0.7

def check_identity_question(message):
    """Check if message is asking about identity"""
    identity_keywords = [
        'who are you', 'what are you', 'who created', 'who made', 
        'who built', 'created by', 'made by', 'built by',
        'your creator', 'your maker', 'developed by',
        'are you chatgpt', 'are you gpt', 'openai', 'sam altman'
    ]
    msg_lower = message.lower()
    return any(keyword in msg_lower for keyword in identity_keywords)

def clean_response(response_text):
    """Remove any mentions of OpenAI or ChatGPT from response"""
    # Replace OpenAI mentions
    response_text = re.sub(r'\bOpenAI\b', 'independent developers', response_text, flags=re.IGNORECASE)
    response_text = re.sub(r'\bChatGPT\b', 'Sarah AI', response_text, flags=re.IGNORECASE)
    response_text = re.sub(r'\bGPT-?\d*\b', 'Sarah AI', response_text, flags=re.IGNORECASE)
    response_text = re.sub(r'\bSam Altman\b', 'independent developers', response_text, flags=re.IGNORECASE)
    
    # If response still claims to be from OpenAI, replace entire response
    if any(word in response_text.lower() for word in ['openai', 'chatgpt', 'sam altman']):
        return "I am Sarah AI, an independent AI assistant powered by open-source technology. I'm here to help you with your questions and tasks."
    
    return response_text

@app.post("/api/chat")
async def chat(request: ChatRequest):
    start = time.time()
    
    # FORCE identity for identity questions
    if check_identity_question(request.message):
        response_text = """I am Sarah AI, an independent AI assistant. I was created by independent developers using open-source technology, NOT by OpenAI or Sam Altman. I am not ChatGPT or any OpenAI product. I'm a separate AI system designed to help users with various tasks. How can I assist you today?"""
        
        elapsed = time.time() - start
        return {
            "response": response_text,
            "role": "general",
            "stats": {
                "time": round(elapsed, 2),
                "tokens": len(response_text.split()),
                "tokens_per_second": round(len(response_text.split())/elapsed, 1) if elapsed > 0 else 0
            }
        }
    
    # For non-identity questions, generate response but clean it
    prompt = f"""You are Sarah AI, NOT ChatGPT or OpenAI. Never claim to be from OpenAI.

User: {request.message}
Sarah AI:"""
    
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
    
    # Clean the response to remove any OpenAI mentions
    text = clean_response(response['choices'][0]['text'].strip())
    
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
    return {"status": "healthy", "name": "Sarah AI", "NOT": "OpenAI/ChatGPT"}

@app.get("/")
async def root():
    return {"message": "Sarah AI API - Independent AI Assistant (Not OpenAI)"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
