"""
NATURAL RESPONSES ONLY - Sarah & Xhash
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
import time
import re
from typing import Optional

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🚀 Loading NATURAL Response Model...")
model = Llama(
    model_path="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
    n_ctx=1024,
    n_threads=4,
    n_batch=256,
    use_mmap=True,
    verbose=False
)
print("✅ Natural Model Ready!")

USERS = {}

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    max_tokens: int = 150
    temperature: float = 0.8

@app.post("/api/chat/with-memory")
async def chat_with_memory(request: ChatRequest):
    start = time.time()
    user_id = request.user_id or f"user_{int(time.time())}"
    
    # Initialize user
    if user_id not in USERS:
        USERS[user_id] = {"gender": "unknown", "name": None, "convos": []}
    
    user = USERS[user_id]
    msg = request.message.lower()
    
    # Detect gender
    if "male" in msg or "man" in msg or "guy" in msg or "boy" in msg:
        user["gender"] = "male"
    elif "female" in msg or "woman" in msg or "girl" in msg or "lady" in msg:
        user["gender"] = "female"
    
    # Extract name
    if "i am" in msg or "i'm" in msg or "im" in msg:
        words = request.message.split()
        for i, word in enumerate(words):
            if word.lower() in ["am", "i'm", "im"] and i+1 < len(words):
                potential_name = words[i+1]
                if potential_name[0].isupper() and potential_name.isalpha():
                    user["name"] = potential_name
                    break
    
    # Build personality
    if user["gender"] == "male":
        personality = "You are Sarah, a sassy woman. Be playfully sarcastic but ALWAYS answer questions properly. Don't just say 'You're trying too hard' - actually engage with the conversation while being sassy."
        persona = "sarah"
    elif user["gender"] == "female":
        personality = "You are Xhash, a confident man. Be charming and engaging. Answer all questions properly while showing confidence."
        persona = "xhash"
    else:
        personality = "You are a helpful AI assistant."
        persona = "neutral"
    
    # Add memory context
    context = ""
    if user["name"]:
        context = f"The user's name is {user['name']}. "
    if len(user["convos"]) > 0:
        last = user["convos"][-1]
        context += f"Last exchange: User said '{last['user']}' and you replied '{last['assistant']}'. "
    
    # Generate NATURAL response
    prompt = f"""{personality}
{context}

User: {request.message}
Assistant:"""
    
    response = model(
        prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        stop=["User:", "\n\n"],
        echo=False
    )
    
    response_text = response['choices'][0]['text'].strip()
    
    # Store conversation
    user["convos"].append({"user": request.message, "assistant": response_text})
    if len(user["convos"]) > 5:
        user["convos"] = user["convos"][-5:]
    
    return {
        "response": response_text,
        "user_id": user_id,
        "memory_size": len(user["convos"]),
        "relationship": {
            "persona": persona,
            "stage": "Active",
            "score": len(user["convos"]) * 10,
            "stage_changed": False,
            "new_stage": None
        },
        "stats": {"time": round(time.time() - start, 2), "context_used": True}
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "name": "NATURAL Sarah & Xhash"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
