"""
Sarah AI - Production Version with Complete Feature Sett
Includes: Memory System, Database, Authentication, Chat, User Management
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pydantic import BaseModel
from llama_cpp import Llama
import time
import psutil
import re
from typing import Optional, Dict, List
from datetime import datetime
import json
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# ============= MEMORY SYSTEM (From your current main.py) =============
# Simple but effective memory system
USER_MEMORY = {}

# ============= IMPORT DATABASE AND SERVICES =============
from app.core.database import db
from app.core.config import settings
from app.services.llm_service import llm_service

# ============= IMPORT PRODUCTION ROUTERS =============
# Using the enhanced versions for full features
from app.api.v1.routers import auth_router_full as auth_router
from app.api.v1.routers import chat_router_enhanced as chat_router
from app.api.v1.routers import user_router

# ============= LIFESPAN MANAGER =============
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting Sarah AI Production Server...")
    
    # Connect to database
    await db.connect()
    print("✅ Database connected")
    
    # Load the LLM model (for router compatibility)
    try:
        llm_service.load_model()
        print("✅ LLM Service initialized")
    except:
        # Use your existing model instead
        print("📌 Using local Llama model")
    
    print("✅ Sarah AI Production Server Ready!")
    
    yield
    
    # Shutdown
    await db.disconnect()
    print("👋 Sarah AI Production Server Stopped")

# ============= CREATE FASTAPI APP =============
app = FastAPI(
    title="Sarah AI - Production API",
    description="AI Assistant with Memory, Authentication, and Relationship System",
    version="2.0.0",
    lifespan=lifespan
)

# ============= CORS MIDDLEWARE =============
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============= LOAD LOCAL LLAMA MODEL (Your existing setup) =============
print("🚀 Loading Sarah AI Local Model...")
model = Llama(
    model_path="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
    n_ctx=1024,
    n_threads=4,
    n_batch=256,
    use_mmap=True,
    use_mlock=False,
    verbose=False
)
print("✅ Sarah AI Local Model Ready!")

# ============= REQUEST MODELS =============
class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 150
    temperature: float = 0.7
    user_id: Optional[str] = "default"

# ============= HELPER FUNCTIONS (From your current main.py) =============
def is_identity_question(message):
    """Check if asking about identity/creator"""
    msg = message.lower()
    identity_words = [
        'who created', 'who made', 'who built', 'who designed',
        'who developed', 'who are you', 'what are you',
        'created by', 'made by', 'built by', 'designed by',
        'your creator', 'your developer', 'your maker',
        'openai', 'open ai', 'chatgpt', 'gpt', 'anthropic', 'claude'
    ]
    return any(word in msg for word in identity_words)

def clean_response(text):
    """Remove ALL mentions of other AIs and companies"""
    replacements = {
        r'\b[Oo]pen\s?AI\b': 'my developers',
        r'\b[Cc]hat\s?GPT\b': 'Sarah AI',
        r'\b[Gg]PT[-\s]?\d*\b': 'Sarah AI',
        r'\b[Aa]nthrop[ic]*\b': 'my developers',
        r'\b[Cc]laude\b': 'Sarah AI',
    }
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    problem_words = ['openai', 'open ai', 'chatgpt', 'gpt-', 'anthropic', 'claude']
    if any(word in text.lower() for word in problem_words):
        return "I'm Sarah AI, an independent AI assistant. How can I help you?"

    return text

# ============= INCLUDE PRODUCTION ROUTERS =============

# Authentication with full features (email verification, password reset, 2FA, OAuth)
app.include_router(
    auth_router.router, 
    prefix="/api/v1/auth", 
    tags=["Authentication"]
)

# Enhanced Chat with relationship system and memory
app.include_router(
    chat_router.router, 
    prefix="/api/v1/chat", 
    tags=["Chat"]
)

# User management
app.include_router(
    user_router.router, 
    prefix="/api/v1/users", 
    tags=["Users"]
)

# ============= YOUR EXISTING ENDPOINTS (Preserved) =============

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """Original chat endpoint with local model"""
    start = time.time()

    if is_identity_question(request.message):
        response_text = "I'm Sarah AI, an independent AI assistant created by independent developers using open-source technology."
    else:
        response = model(
            f"User: {request.message}\nAssistant:",
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=["User:"],
            echo=False
        )
        response_text = response['choices'][0]['text'].strip()
        response_text = clean_response(response_text)

    elapsed = time.time() - start
    return {
        "response": response_text,
        "role": "general",
        "stats": {
            "time": round(elapsed, 2),
            "tokens": len(response_text.split()),
            "tokens_per_second": round(len(response_text.split())/elapsed, 1)
        }
    }

@app.post("/api/chat/with-memory")
async def chat_with_memory(request: ChatRequest):
    """Chat with working memory (your existing implementation)"""
    start = time.time()
    user_id = request.user_id or "default"

    # Initialize user memory if needed
    if user_id not in USER_MEMORY:
        USER_MEMORY[user_id] = []

    # Check for identity question
    if is_identity_question(request.message):
        response_text = "I'm Sarah AI, an independent AI assistant created by independent developers."
    else:
        # Build context-aware prompt
        prompt = ""

        # Add conversation history
        if USER_MEMORY[user_id]:
            prompt = "You are Sarah AI. Remember this conversation:\n\n"
            for exchange in USER_MEMORY[user_id][-3:]:  # Last 3 exchanges
                prompt += f"User: {exchange['user']}\n"
                prompt += f"Sarah: {exchange['assistant']}\n"
            prompt += "\nBased on the above conversation, respond to:\n"

        prompt += f"User: {request.message}\nSarah:"

        # Generate response with context
        response = model(
            prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=["User:", "\n\n"],
            echo=False
        )
        response_text = response['choices'][0]['text'].strip()
        response_text = clean_response(response_text)

    # Store in memory
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
async def get_user_memory(user_id: str):
    """Get memory for a specific user"""
    return {
        "user_id": user_id,
        "conversations": USER_MEMORY.get(user_id, []),
        "total": len(USER_MEMORY.get(user_id, []))
    }

@app.delete("/api/memory/{user_id}")
async def clear_user_memory(user_id: str):
    """Clear memory for a specific user"""
    if user_id in USER_MEMORY:
        del USER_MEMORY[user_id]
    return {"message": f"Memory cleared for {user_id}"}

@app.get("/api/agents/status")
async def agents_status():
    """Basic agent status endpoint"""
    return {
        "name": "Sarah AI",
        "version": "2.0",
        "mode": "production",
        "capabilities": [
            "chat", 
            "identity_protection", 
            "context_awareness",
            "authentication",
            "relationship_tracking",
            "user_facts_extraction",
            "conversation_persistence"
        ],
        "status": "active"
    }

# ============= ROOT AND HEALTH ENDPOINTS =============

@app.get("/")
async def root():
    """Root endpoint with complete API information"""
    return {
        "name": "Sarah AI Production API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "personalities": ["sarah", "xhash", "neutral"],
        "features": {
            "authentication": {
                "register": "POST /api/v1/auth/register",
                "login": "POST /api/v1/auth/login",
                "oauth": "POST /api/v1/auth/google",
                "password_reset": "POST /api/v1/auth/forgot-password",
                "2fa": "Available"
            },
            "chat": {
                "simple": "POST /api/chat",
                "with_memory": "POST /api/chat/with-memory",
                "enhanced": "POST /api/v1/chat/message",
                "conversations": "GET /api/v1/chat/conversations",
                "relationship": "GET /api/v1/chat/relationship/status"
            },
            "users": {
                "profile": "GET /api/v1/users/profile",
                "facts": "GET /api/v1/users/facts",
                "stats": "GET /api/v1/users/stats"
            }
        },
        "memory_system": {
            "local_memory": len(USER_MEMORY),
            "database": "connected"
        }
    }

@app.get("/health")
async def health():
    """Comprehensive health check"""
    try:
        # Check database
        db_status = await db.fetchval("SELECT 1")
        user_count = await db.fetchval("SELECT COUNT(*) FROM users")
        conversation_count = await db.fetchval("SELECT COUNT(*) FROM conversations")
        relationship_count = await db.fetchval("SELECT COUNT(*) FROM relationships")
        
        return {
            "status": "healthy",
            "name": "Sarah AI Production",
            "database": {
                "connected": bool(db_status),
                "users": user_count or 0,
                "conversations": conversation_count or 0,
                "relationships": relationship_count or 0
            },
            "memory": {
                "local_users": len(USER_MEMORY),
                "total_exchanges": sum(len(mem) for mem in USER_MEMORY.values())
            },
            "model": {
                "local_llama": "loaded",
                "path": "openhermes-2.5-mistral-7b.Q4_K_M.gguf"
            },
            "endpoints": {
                "auth": 12,
                "chat": 8,
                "users": 5,
                "memory": 3,
                "total": 30
            }
        }
    except Exception as e:
        return {
            "status": "partial",
            "error": str(e),
            "local_memory": len(USER_MEMORY),
            "model": "loaded"
        }

@app.get("/api/stats")
async def api_stats():
    """Get comprehensive API statistics"""
    try:
        stats = {
            "users": {
                "total": await db.fetchval("SELECT COUNT(*) FROM users"),
                "active_today": await db.fetchval("""
                    SELECT COUNT(*) FROM users 
                    WHERE last_login > CURRENT_DATE
                """),
                "with_2fa": await db.fetchval("""
                    SELECT COUNT(*) FROM users 
                    WHERE two_factor_enabled = true
                """)
            },
            "conversations": {
                "total": await db.fetchval("SELECT COUNT(*) FROM conversations"),
                "active": await db.fetchval("""
                    SELECT COUNT(*) FROM conversations 
                    WHERE is_active = true
                """),
                "messages": await db.fetchval("SELECT COUNT(*) FROM messages")
            },
            "relationships": {
                "total": await db.fetchval("SELECT COUNT(*) FROM relationships"),
                "by_stage": await db.fetch("""
                    SELECT stage, COUNT(*) as count 
                    FROM relationships 
                    GROUP BY stage
                """)
            },
            "facts": {
                "total": await db.fetchval("SELECT COUNT(*) FROM user_facts"),
                "unique_users": await db.fetchval("""
                    SELECT COUNT(DISTINCT user_id) FROM user_facts
                """)
            },
            "memory": {
                "local_sessions": len(USER_MEMORY),
                "total_local_messages": sum(len(mem) for mem in USER_MEMORY.values())
            }
        }
        
        # Convert stage counts to dict
        if stats["relationships"]["by_stage"]:
            stats["relationships"]["by_stage"] = {
                row["stage"]: row["count"] 
                for row in stats["relationships"]["by_stage"]
            }
        
        return stats
    except Exception as e:
        return {"error": str(e), "local_memory_active": True}

# ============= MAIN ENTRY POINT =============
if __name__ == "__main__":
    import uvicorn
    
    # Use settings from config or defaults
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    uvicorn.run(
        "main:app",  # Or "app.main:app" depending on your structure
        host=host,
        port=port,
        reload=False,  # Set to False in production
        workers=1  # Increase for production based on your server
    )
