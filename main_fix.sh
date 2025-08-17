#!/bin/bash

# Save this as fix_main.sh and run it on your server

cat > /root/openhermes_backend/main_fixed.py << 'EOF'
"""
OpenHermes 2.5 - Fast Commercial Version
Using llama.cpp for 3-5x faster inference
Apache 2.0 License - Commercial use allowed
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
from llama_cpp import Llama
import time
import json
import psutil

# Import metrics module (renamed from metrics_module to comprehensive_metrics)
from comprehensive_metrics import metrics_collector

app = FastAPI(
    title="OpenHermes Commercial API",
    description="Fast OpenHermes 2.5 - Apache 2.0 Licensed",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model variable
llm = None

class ChatRequest(BaseModel):
    message: str
    agent_role: Optional[str] = "general"
    max_tokens: Optional[int] = 150
    temperature: Optional[float] = 0.7

def initialize_model():
    """Initialize OpenHermes with llama.cpp for fast inference"""
    global llm

    try:
        print("🚀 Loading OpenHermes 2.5 (Commercial Version)...")
        print("📜 License: Apache 2.0 - Commercial use permitted")

        llm = Llama(
            model_path="openhermes-2.5-mistral-7b.Q4_K_M.gguf",
            n_ctx=2048,  # Context window
            n_threads=8,  # Use 8 CPU threads for speed
            n_batch=512,  # Larger batch for speed
            n_gpu_layers=0,  # CPU only (set to 20+ if you have GPU)
            verbose=False,
            seed=-1,
            f16_kv=True,  # Use half precision for speed
            use_mlock=False,  # Don't lock memory
            embedding=False  # We don't need embeddings
        )

        print("✅ OpenHermes loaded successfully!")
        print("⚡ Optimized for fast inference (3-8 seconds per response)")

        # Warm up the model
        print("🔥 Warming up model...")
        llm("Hello", max_tokens=10)
        print("✅ Model ready for production use!")

    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("Make sure openhermes-2.5-mistral-7b.Q4_K_M.gguf is in the current directory")

@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    initialize_model()

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "OpenHermes Commercial API",
        "model": "OpenHermes-2.5-Mistral-7B",
        "version": "Q4_K_M (4-bit quantized)",
        "license": "Apache 2.0",
        "commercial_use": "Yes - Permitted",
        "endpoints": {
            "chat": "/api/chat",
            "health": "/health",
            "metrics": "/metrics"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": llm is not None,
        "model": "OpenHermes-2.5-Mistral-7B-GGUF",
        "quantization": "Q4_K_M",
        "commercial_use": "permitted"
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint - Fast inference with llama.cpp"""

    if not llm:
        return {
            "response": "Model is still loading, please wait...",
            "role": "system"
        }

    try:
        print(f"📨 Processing: {request.message[:50]}...")
        start_time = time.time()

        # Format prompt for better responses
        if request.agent_role == "software_engineer":
            system_prompt = "You are an expert software engineer. Provide clear, concise code examples and explanations."
        elif request.agent_role == "data_analyst":
            system_prompt = "You are a data analyst. Focus on insights and data-driven recommendations."
        else:
            system_prompt = "You are a helpful AI assistant. Provide clear and concise responses."

        # OpenHermes format
        prompt = f"""<|im_start|>system
{system_prompt}
<|im_end|>
<|im_start|>user
{request.message}
<|im_end|>
<|im_start|>assistant
"""

        # Generate response with llama.cpp (FAST!)
        output = llm(
            prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=0.95,
            repeat_penalty=1.1,
            top_k=40,
            stop=["<|im_end|>", "<|im_start|>", "User:", "\n\n\n"],
            echo=False
        )

        response_text = output['choices'][0]['text'].strip()

        # Clean up any remaining tokens
        response_text = response_text.replace("<|im_end|>", "").strip()

        elapsed = time.time() - start_time
        tokens_per_second = output['usage']['completion_tokens'] / elapsed if elapsed > 0 else 0

        print(f"✅ Generated {output['usage']['completion_tokens']} tokens in {elapsed:.1f}s ({tokens_per_second:.1f} tok/s)")

        # Record metrics for this request
        metrics_collector.record_request(elapsed, output['usage']['completion_tokens'], success=True)

        return {
            "response": response_text,
            "role": request.agent_role or "ai",
            "stats": {
                "time": round(elapsed, 2),
                "tokens": output['usage']['completion_tokens'],
                "tokens_per_second": round(tokens_per_second, 1)
            }
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        # Record failed request
        metrics_collector.record_request(0, 0, success=False)
        return {
            "response": f"Error processing request: {str(e)}",
            "role": "system"
        }

@app.get("/metrics")
async def get_basic_metrics():
    """Basic system metrics endpoint"""
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory": {
            "percent": psutil.virtual_memory().percent,
            "available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "used_gb": round(psutil.virtual_memory().used / (1024**3), 2),
        },
        "model": {
            "loaded": llm is not None,
            "name": "OpenHermes-2.5-Mistral-7B",
            "quantization": "Q4_K_M",
            "size_gb": 4.4
        }
    }

@app.get("/agents")
async def get_agents():
    """Get available agent roles"""
    return [
        {"role": "general", "name": "General Assistant"},
        {"role": "software_engineer", "name": "Software Engineer"},
        {"role": "data_analyst", "name": "Data Analyst"},
        {"role": "devops_engineer", "name": "DevOps Engineer"}
    ]

# ============= COMPREHENSIVE METRICS ENDPOINTS =============

@app.get("/metrics/system")
async def metrics_system():
    """Get all system metrics matching frontend SystemMetrics interface"""
    return metrics_collector.get_system_metrics()

@app.get("/metrics/ai")
async def metrics_ai():
    """Get AI-specific metrics"""
    data = metrics_collector.get_system_metrics()
    return {
        "accuracy": data["accuracy"],
        "throughput": data["throughput"],
        "latency": data["latency"],
        "gpuUtilization": data["gpuUtilization"],
        "memoryUsage": data["memoryUsage"],
        "activeModels": data["activeModels"]
    }

@app.get("/metrics/components")
async def metrics_components():
    """Get system components status"""
    return metrics_collector.get_system_components()

@app.get("/metrics/pipeline")
async def metrics_pipeline():
    """Get pipeline status"""
    return metrics_collector.get_pipeline_status()

@app.get("/metrics/executive")
async def metrics_executive():
    """Get executive dashboard metrics"""
    data = metrics_collector.get_system_metrics()
    return {
        "metrics": {
            "revenue": data["revenue"],
            "growth": data["growth"],
            "customers": data["customers"],
            "marketShare": data["marketShare"],
            "satisfaction": data["satisfaction"],
            "employees": data["employees"]
        },
        "initiatives": [
            {"name": "AI Platform Expansion", "progress": 75, "status": "on-track"},
            {"name": "Global Market Entry", "progress": 45, "status": "on-track"},
            {"name": "Product Innovation", "progress": 60, "status": "ahead"},
            {"name": "Customer Success Program", "progress": 85, "status": "on-track"}
        ],
        "regions": [
            {"region": "North America", "revenue": 45000, "growth": 18},
            {"region": "Europe", "revenue": 35000, "growth": 22},
            {"region": "Asia Pacific", "revenue": 30000, "growth": 35},
            {"region": "Latin America", "revenue": 15000, "growth": 28}
        ],
        "kpis": [
            {"metric": "Customer Acquisition", "value": "+250", "trend": "up"},
            {"metric": "Revenue Growth", "value": "+18%", "trend": "up"},
            {"metric": "Market Share", "value": "12.5%", "trend": "up"},
            {"metric": "NPS Score", "value": "72", "trend": "up"}
        ]
    }

@app.get("/metrics/financial")
async def metrics_financial():
    """Get financial metrics"""
    data = metrics_collector.get_system_metrics()
    return {
        "metrics": {
            "profit": data["profit"],
            "cashFlow": data["cashFlow"],
            "expenses": data["expenses"],
            "roi": data["roi"],
            "burnRate": data["burnRate"]
        },
        "budget": [
            {"category": "R&D", "allocated": 50000, "spent": 42000, "variance": 16},
            {"category": "Marketing", "allocated": 30000, "spent": 28500, "variance": 5},
            {"category": "Operations", "allocated": 25000, "spent": 24000, "variance": 4},
            {"category": "Sales", "allocated": 20000, "spent": 19500, "variance": 2.5}
        ],
        "investments": [
            {"investment": "AI Infrastructure", "value": 500000, "return": 22},
            {"investment": "Cloud Services", "value": 200000, "return": 18},
            {"investment": "Security", "value": 150000, "return": 15},
            {"investment": "Marketing Tech", "value": 100000, "return": 25}
        ]
    }

@app.get("/metrics/marketing")
async def metrics_marketing():
    """Get marketing metrics"""
    data = metrics_collector.get_system_metrics()
    return {
        "metrics": {
            "cac": data["cac"],
            "ltv": data["ltv"],
            "conversion": data["conversion"],
            "engagement": data["engagement"],
            "reach": data["reach"],
            "brandAwareness": data["brandAwareness"]
        },
        "campaigns": [
            {"name": "AI Innovation 2024", "budget": 50000, "spent": 35000, "performance": 125, "status": "active"},
            {"name": "Developer Outreach", "budget": 30000, "spent": 22000, "performance": 110, "status": "active"},
            {"name": "Enterprise Solutions", "budget": 40000, "spent": 38000, "performance": 95, "status": "completed"}
        ],
        "channels": [
            {"channel": "Digital", "traffic": 45000, "conversion": 3.5, "roi": 250},
            {"channel": "Social Media", "traffic": 35000, "conversion": 2.8, "roi": 180},
            {"channel": "Email", "traffic": 25000, "conversion": 4.2, "roi": 320},
            {"channel": "Direct", "traffic": 15000, "conversion": 5.5, "roi": 400}
        ],
        "brandMetrics": [
            {"metric": "Brand Recognition", "value": 78, "trend": "up"},
            {"metric": "Customer Loyalty", "value": 85, "trend": "up"},
            {"metric": "Market Position", "value": 3, "trend": "up"}
        ]
    }

@app.get("/metrics/technology")
async def metrics_technology():
    """Get technology metrics"""
    data = metrics_collector.get_system_metrics()
    return {
        "metrics": {
            "deployments": data["deployments"],
            "codeQuality": data["codeQuality"],
            "security": data["security"],
            "performance": data["performance"],
            "infrastructure": data["infrastructure"]
        },
        "codeStats": [
            {"metric": "Lines of Code", "value": "2.5M", "change": "+5%"},
            {"metric": "Test Coverage", "value": "92%", "change": "+2%"},
            {"metric": "Technical Debt", "value": "Low", "change": "-10%"}
        ],
        "teamProductivity": [
            {"metric": "Velocity", "value": "85 pts", "change": "+8%"},
            {"metric": "Cycle Time", "value": "3.2 days", "change": "-15%"},
            {"metric": "Deploy Frequency", "value": "12/week", "change": "+20%"}
        ],
        "infrastructure": [
            {"service": "API Gateway", "status": "healthy", "load": 45},
            {"service": "Model Server", "status": "healthy", "load": 68},
            {"service": "Database", "status": "healthy", "load": 35},
            {"service": "Cache", "status": "healthy", "load": 28}
        ],
        "security": [
            {"check": "Vulnerability Scan", "status": "passed", "lastRun": "2 hours ago"},
            {"check": "Access Audit", "status": "passed", "lastRun": "1 day ago"},
            {"check": "Compliance Check", "status": "passed", "lastRun": "3 days ago"}
        ]
    }

@app.get("/metrics/operations")
async def metrics_operations():
    """Get operations metrics"""
    data = metrics_collector.get_system_metrics()
    return {
        "metrics": {
            "efficiency": data["efficiency"],
            "quality": data["quality"],
            "onTime": data["onTime"],
            "utilization": data["utilization"],
            "incidents": data["incidents"]
        },
        "productionLines": [
            {"line": "Model Training", "efficiency": 92, "output": 1250, "status": "optimal"},
            {"line": "Data Processing", "efficiency": 88, "output": 2500, "status": "good"},
            {"line": "Inference Pipeline", "efficiency": 95, "output": 5000, "status": "optimal"}
        ],
        "suppliers": [
            {"supplier": "Cloud Provider A", "delivery": 99.9, "quality": 98, "cost": "optimal"},
            {"supplier": "GPU Provider", "delivery": 98.5, "quality": 99, "cost": "good"},
            {"supplier": "Data Provider", "delivery": 97, "quality": 95, "cost": "acceptable"}
        ],
        "performanceMetrics": [
            {"metric": "SLA Compliance", "value": 99.5, "target": 99},
            {"metric": "Response Time", "value": 1.2, "target": 2},
            {"metric": "Error Rate", "value": 0.5, "target": 1}
        ]
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Rename metrics_module.py to comprehensive_metrics.py if it exists
if [ -f "/root/openhermes_backend/metrics_module.py" ]; then
    mv /root/openhermes_backend/metrics_module.py /root/openhermes_backend/comprehensive_metrics.py
    echo "✅ Renamed metrics_module.py to comprehensive_metrics.py"
fi

# Backup old main.py and replace with fixed version
cp /root/openhermes_backend/main.py /root/openhermes_backend/main_backup.py
mv /root/openhermes_backend/main_fixed.py /root/openhermes_backend/main.py

echo "✅ main.py has been fixed with:"
echo "- Moved import to top of file"
echo "- Fixed import name (comprehensive_metrics)"
echo "- Added psutil import"
echo "- Integrated metrics recording in chat endpoint"
echo "- Removed duplicate/misplaced code"
echo "- All metrics endpoints properly defined"
echo ""
echo "Now restart the service:"
echo "sudo systemctl restart openhermes"
