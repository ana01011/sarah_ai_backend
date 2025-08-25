"""
Sarah AI - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import our modules
from app.core.database import db
from app.core.config import settings
from app.services.llm_service import llm_service

# Import routers
from app.api.v1.routers import auth_router, chat_router, user_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting Sarah AI Backend...")
    await db.connect()
    llm_service.load_model()
    print("✅ Sarah AI Backend Started")
    
    yield
    
    # Shutdown
    await db.disconnect()
    print("👋 Sarah AI Backend Stopped")

# Create FastAPI app
app = FastAPI(
    title="Sarah AI API",
    description="AI Chat with Multiple Personalities",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(chat_router.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(user_router.router, prefix="/api/v1/users", tags=["Users"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Sarah AI API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "personalities": ["sarah", "xhash", "neutral"]
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Check database
        db_status = await db.fetchval("SELECT 1")
        
        # Count users
        user_count = await db.fetchval("SELECT COUNT(*) FROM users")
        
        return {
            "status": "healthy",
            "database": "connected" if db_status else "disconnected",
            "model": "loaded" if llm_service.model else "not loaded",
            "users": user_count or 0
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
