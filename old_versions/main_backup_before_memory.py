"""
Sarah AI - Complete Identity Fix with Enhanced Agent Capabilities
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from llama_cpp import Llama
import time
import psutil
import re
from typing import Optional, List, Dict, Any
from enum import Enum
import asyncio
from datetime import datetime

# ============= ENHANCED SARAH AI IMPORTS =============
try:
    from app.agents.sarah_ai import SarahAI, PersonalityMode
    from app.agents.memory_manager import MemoryManager
    from app.agents.tools import ToolSystem
    from app.agents.intent_router import IntentRouter
    ENHANCED_MODE = True
except ImportError:
    ENHANCED_MODE = False
    print("⚠️ Enhanced modules not found. Running in basic mode.")

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
except:
    pass

print("🚀 Loading Sarah AI...")
model = Llama(
    model_path="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
    n_ctx=1024,
    n_threads=4,
    n_batch=256,
    use_mmap=True,
    use_mlock=True,
    verbose=False
)
print("✅ Sarah AI Ready!")

# ============= INITIALIZE ENHANCED COMPONENTS =============
if ENHANCED_MODE:
    print("🎯 Initializing Enhanced Sarah AI Components...")
    sarah_ai = SarahAI()
    memory_manager = MemoryManager()
    tool_system = ToolSystem()
    intent_router = IntentRouter()
    print("✨ Enhanced mode activated!")

class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 150
    temperature: float = 0.7
    user_id: Optional[str] = "default"
    mode: Optional[str] = None

def is_identity_question(message):
    """Check if asking about identity/creator"""
    msg = message.lower()
    identity_words = [
        'who created', 'who made', 'who built', 'who designed',
        'who developed', 'who are you', 'what are you',
        'created by', 'made by', 'built by', 'designed by',
        'your creator', 'your developer', 'your maker',
        'openai', 'open ai', 'chatgpt', 'gpt', 'anthropic', 'claude',
        'who owns you', 'who maintains you', 'where are you from',
        'what company', 'which company', 'what organization'
    ]
    return any(word in msg for word in identity_words)

def clean_response(text):
    """Remove ALL mentions of other AIs and companies"""
    # List of replacements
    replacements = {
        r'\b[Oo]pen\s?AI\b': 'my developers',
        r'\b[Cc]hat\s?GPT\b': 'Sarah AI',
        r'\b[Gg]PT[-\s]?\d*\b': 'Sarah AI',
        r'\b[Aa]nthrop[ic]*\b': 'my developers',
        r'\b[Cc]laude\b': 'Sarah AI',
        r'\b[Mm]icrosoft\b': 'my developers',
        r'\b[Gg]oogle\b': 'my developers',
        r'Yes, I am the Open AI': 'I am Sarah AI',
        r'I am a text-based AI model created by': 'I am Sarah AI, created by',
        r'Open AI Product': 'Sarah AI',
    }

    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    # If still contains problematic words, return safe response
    problem_words = ['openai', 'open ai', 'chatgpt', 'gpt-', 'anthropic', 'claude']
    if any(word in text.lower() for word in problem_words):
        return "I'm Sarah AI, an independent AI assistant created by independent developers using open-source technology. How can I help you?"

    return text

@app.post("/api/chat")
async def chat(request: ChatRequest):
    start = time.time()

    # Check if identity question
    if is_identity_question(request.message):
        # Always return consistent identity
        response_text = "I'm Sarah AI, an independent AI assistant created by independent developers using open-source technology. I'm not associated with OpenAI, Anthropic, or any major tech company. I'm here to help you with your questions and tasks."
    else:
        # Generate response for non-identity questions
        response = model(
            f"User: {request.message}\nAssistant:",
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=["User:"],
            echo=False
        )
        response_text = response['choices'][0]['text'].strip()

        # Clean any problematic mentions
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

# ============= ENHANCED SARAH AI ENDPOINTS =============
if ENHANCED_MODE:
    @app.post("/api/chat/enhanced")
    async def enhanced_chat(request: ChatRequest):
        """Enhanced chat endpoint with full agent capabilities"""
        start_time = time.time()
        
        try:
            # Check for identity questions first
            if is_identity_question(request.message):
                response_text = "I'm Sarah AI, an independent AI assistant created by independent developers using open-source technology. I'm not associated with OpenAI, Anthropic, or any major tech company. I'm here to help you with your questions and tasks."
                suggestions = ["What can I help you with today?", "Ask me anything!", "How can I assist you?"]
            else:
                # Get user context
                context = await memory_manager.get_relevant_context(request.message, request.user_id)
                
                # Detect intent and route
                intent, confidence = await intent_router.detect_intent(request.message)
                target_agent = await intent_router.route_to_agent(request.message)
                
                # Set personality mode if specified
                if request.mode:
                    try:
                        sarah_ai.personality_mode = PersonalityMode(request.mode)
                    except:
                        pass
                
                # Generate response using the model
                prompt = sarah_ai.format_prompt(request.message)
                response = model(
                    prompt,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    stop=["User:", "<|im_end|>"],
                    echo=False
                )
                response_text = response['choices'][0]['text'].strip()
                
                # Clean response
                response_text = clean_response(response_text)
                
                # Enhance response based on personality
                response_text = await sarah_ai.enhance_response(response_text, sarah_ai.personality_mode)
                
                # Generate suggestions
                suggestions = await sarah_ai.generate_suggestions(request.message, response_text)
                
                # Update memory
                await memory_manager.add_interaction(
                    request.user_id,
                    request.message,
                    response_text,
                    {
                        "intent": intent.value if hasattr(intent, 'value') else str(intent),
                        "confidence": confidence,
                        "agent": target_agent,
                        "personality_mode": sarah_ai.personality_mode.value
                    }
                )
            
            # Calculate metrics
            processing_time = time.time() - start_time
            
            return {
                "response": response_text,
                "agent": "Sarah AI",
                "role": f"Intelligent Assistant ({sarah_ai.personality_mode.value})",
                "confidence": 0.95,
                "suggestions": suggestions,
                "metadata": {
                    "processing_time": round(processing_time, 2),
                    "personality_mode": sarah_ai.personality_mode.value,
                    "enhanced_mode": True
                }
            }
            
        except Exception as e:
            # Fallback to basic mode
            print(f"Enhanced mode error: {e}")
            return await chat(request)

    @app.get("/api/agents/sarah/status")
    async def sarah_status():
        """Get Sarah AI status and capabilities"""
        return {
            "name": "Sarah AI",
            "version": "2.0",
            "personality_modes": [mode.value for mode in PersonalityMode],
            "current_mode": sarah_ai.personality_mode.value,
            "capabilities": sarah_ai.capabilities,
            "memory": {
                "short_term_count": len(sarah_ai.short_term_memory),
                "long_term_count": len(sarah_ai.long_term_memory)
            },
            "tools": list(tool_system.tools.keys()),
            "status": "active",
            "enhanced_mode": True
        }

    @app.post("/api/agents/sarah/personality")
    async def set_personality(request: Dict[str, str]):
        """Set Sarah's personality mode"""
        try:
            mode = request.get("mode")
            sarah_ai.personality_mode = PersonalityMode(mode)
            return {"success": True, "mode": mode}
        except:
            return {"success": False, "error": "Invalid personality mode"}

    @app.get("/api/agents/sarah/memory")
    async def get_memory_status():
        """Get memory status"""
        return {
            "short_term": len(memory_manager.short_term),
            "user_profiles": len(memory_manager.user_profiles),
            "conversation_summary": memory_manager.get_conversation_summary()
        }

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "name": "Sarah AI", 
        "identity": "Independent AI",
        "enhanced_mode": ENHANCED_MODE
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# ============= ENHANCED SARAH AI ENDPOINTS =============
from typing import Optional, Dict
import asyncio
from datetime import datetime

# Import enhanced modules
try:
    from app.agents.sarah_ai import SarahAI, PersonalityMode
    from app.agents.memory_manager import MemoryManager
    from app.agents.tools import ToolSystem
    from app.agents.intent_router import IntentRouter
    
    # Initialize enhanced components
    sarah_ai = SarahAI()
    memory_manager = MemoryManager()
    tool_system = ToolSystem()
    intent_router = IntentRouter()
    ENHANCED_MODE = True
    print("✨ Enhanced Sarah AI modules loaded!")
except ImportError as e:
    ENHANCED_MODE = False
    print(f"⚠️ Enhanced modules not loaded: {e}")

# Update ChatRequest to include optional fields
class EnhancedChatRequest(BaseModel):
    message: str
    max_tokens: int = 150
    temperature: float = 0.7
    user_id: Optional[str] = "default"
    mode: Optional[str] = None

if ENHANCED_MODE:
    @app.post("/api/chat/enhanced")
    async def enhanced_chat(request: EnhancedChatRequest):
        """Enhanced chat endpoint with full agent capabilities"""
        start_time = time.time()
        
        try:
            # Check for identity questions first
            if is_identity_question(request.message):
                response_text = "I'm Sarah AI, an independent AI assistant created by independent developers using open-source technology."
                suggestions = ["What can I help you with?", "Ask me anything!", "How can I assist?"]
            else:
                # Generate response using the model with enhanced context
                response = model(
                    f"User: {request.message}\nAssistant:",
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    stop=["User:"],
                    echo=False
                )
                response_text = response['choices'][0]['text'].strip()
                response_text = clean_response(response_text)
                
                # Generate suggestions
                suggestions = ["Tell me more", "What else can I help with?", "Any other questions?"]
                
                # Update memory
                await memory_manager.add_interaction(
                    request.user_id,
                    request.message,
                    response_text,
                    {"timestamp": datetime.now().isoformat()}
                )
            
            elapsed = time.time() - start_time
            
            return {
                "response": response_text,
                "agent": "Sarah AI",
                "role": "Intelligent Assistant",
                "suggestions": suggestions,
                "metadata": {
                    "processing_time": round(elapsed, 2),
                    "enhanced_mode": True,
                    "user_id": request.user_id
                }
            }
        except Exception as e:
            print(f"Enhanced chat error: {e}")
            # Fallback to basic response
            return {
                "response": "I encountered an issue. Please try again.",
                "error": str(e)
            }

    @app.get("/api/agents/sarah/status")
    async def sarah_status():
        """Get Sarah AI status and capabilities"""
        return {
            "name": "Sarah AI",
            "version": "2.0",
            "personality_modes": ["professional", "friendly", "technical", "creative", "teacher"],
            "current_mode": "friendly",
            "capabilities": {
                "chat": True,
                "memory": True,
                "tools": True,
                "personality": True
            },
            "memory": {
                "short_term_count": len(memory_manager.short_term) if hasattr(memory_manager, 'short_term') else 0,
                "user_profiles": len(memory_manager.user_profiles) if hasattr(memory_manager, 'user_profiles') else 0
            },
            "status": "active"
        }

    @app.post("/api/agents/sarah/personality")
    async def set_personality(request: Dict):
        """Set Sarah's personality mode"""
        try:
            mode = request.get("mode", "friendly")
            # For now, just acknowledge the mode change
            return {"success": True, "mode": mode, "message": f"Personality set to {mode}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @app.get("/api/agents/sarah/memory")
    async def get_memory_status():
        """Get memory status"""
        return {
            "short_term": len(memory_manager.short_term) if hasattr(memory_manager, 'short_term') else 0,
            "user_profiles": len(memory_manager.user_profiles) if hasattr(memory_manager, 'user_profiles') else 0,
            "status": "active"
        }
else:
    # Provide basic fallback endpoints
    @app.get("/api/agents/sarah/status")
    async def sarah_status_basic():
        return {
            "name": "Sarah AI",
            "version": "1.0",
            "enhanced_mode": False,
            "status": "basic mode"
        }

# ============= END ENHANCED ENDPOINTS =============
