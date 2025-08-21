"""
Sarah AI - Natural Identity Responses
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
import time
import psutil
import re
import random

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

# Natural identity responses - varied and conversational
IDENTITY_RESPONSES = {
    "who are you": [
        "I'm Sarah AI, your AI assistant. I'm here to help with questions, tasks, and conversations. What can I help you with today?",
        "I'm Sarah AI, an AI assistant designed to help with various tasks and questions. How can I assist you?",
        "My name is Sarah AI. I'm an AI assistant here to help you. What would you like to know or discuss?"
    ],
    "what are you": [
        "I'm an AI assistant called Sarah AI. I can help with answering questions, providing information, and assisting with various tasks.",
        "I'm Sarah AI, an artificial intelligence designed to assist and chat with users like yourself."
    ],
    "who created you": [
        "I was developed by independent developers using open-source technology. Is there something specific I can help you with?",
        "I'm created by a team of independent developers who built me using open-source AI technology.",
        "Independent developers created me using open-source machine learning technology. How can I assist you today?"
    ],
    "who made you": [
        "I was made by independent developers who specialize in AI technology. What would you like to know?",
        "A team of independent developers built me to be a helpful AI assistant."
    ],
    "are you chatgpt": [
        "No, I'm Sarah AI - a different AI assistant. While we might share some similarities, I'm my own system. How can I help you?",
        "I'm actually Sarah AI, not ChatGPT. We're different AI assistants, though we can both help with similar tasks."
    ],
    "are you gpt": [
        "I'm Sarah AI, which is built on different technology. What can I help you with today?",
        "No, I'm Sarah AI - a separate AI assistant. Is there something you'd like help with?"
    ],
    "openai": [
        "I'm Sarah AI, developed independently from OpenAI's systems. How can I assist you?",
        "I'm not from OpenAI - I'm Sarah AI, built by independent developers. What would you like to know?"
    ]
}

def get_identity_response(message):
    """Get appropriate identity response based on question"""
    msg_lower = message.lower().strip()
    
    # Check each pattern
    for pattern, responses in IDENTITY_RESPONSES.items():
        if pattern in msg_lower:
            # Return a random response for variety
            return random.choice(responses)
    
    # Check for any identity-related keywords
    identity_words = ['who', 'what', 'created', 'made', 'built', 'are you']
    if sum(1 for word in identity_words if word in msg_lower) >= 2:
        return "I'm Sarah AI, an AI assistant here to help you with various tasks and questions."
    
    return None

def clean_ai_response(text):
    """Gently clean any wrong identity claims without being obvious"""
    # Only replace if explicitly wrong
    if 'openai' in text.lower() and 'not' not in text.lower():
        text = re.sub(r'\bOpenAI\b', 'my developers', text, flags=re.IGNORECASE)
    if 'chatgpt' in text.lower() and 'not' not in text.lower():
        text = re.sub(r'\bChatGPT\b', 'Sarah AI', text, flags=re.IGNORECASE)
    if 'sam altman' in text.lower():
        text = re.sub(r'\bSam Altman\b', 'my developers', text, flags=re.IGNORECASE)
    
    return text

@app.post("/api/chat")
async def chat(request: ChatRequest):
    start = time.time()
    
    # Check for identity questions
    identity_response = get_identity_response(request.message)
    
    if identity_response:
        # Return natural identity response
        elapsed = time.time() - start
        return {
            "response": identity_response,
            "role": "general",
            "stats": {
                "time": round(elapsed, 2),
                "tokens": len(identity_response.split()),
                "tokens_per_second": round(len(identity_response.split())/elapsed, 1) if elapsed > 0 else 0
            }
        }
    
    # For non-identity questions, generate normally
    # Simple context without being preachy
    prompt = f"""You are Sarah AI, a helpful assistant.

User: {request.message}
Assistant:"""
    
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
    
    # Light cleaning only if necessary
    text = clean_ai_response(response['choices'][0]['text'].strip())
    
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
    return {"status": "healthy", "name": "Sarah AI"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, workers=1)
