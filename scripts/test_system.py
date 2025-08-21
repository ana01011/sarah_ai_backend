#!/usr/bin/env python3
"""
Sarah AI System Test Script
Tests all major components to ensure the system is ready
"""

import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Colors for terminal output
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_header(text):
    """Print a formatted header"""
    print(f"\n{BLUE}{'='*50}{NC}")
    print(f"{BLUE}{text}{NC}")
    print(f"{BLUE}{'='*50}{NC}")

def print_success(text):
    """Print success message"""
    print(f"{GREEN}✓ {text}{NC}")

def print_error(text):
    """Print error message"""
    print(f"{RED}✗ {text}{NC}")

def print_warning(text):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{NC}")

def print_info(text):
    """Print info message"""
    print(f"  {text}")

async def test_database():
    """Test database connectivity"""
    print_header("Testing Database Connection")
    
    try:
        # Get database credentials
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = int(os.getenv("POSTGRES_PORT", 5432))
        user = os.getenv("POSTGRES_USER", "sarah_user")
        password = os.getenv("POSTGRES_PASSWORD", "sarah_secure_2024")
        database = os.getenv("POSTGRES_DB", "sarah_ai_fresh")
        
        print_info(f"Host: {host}:{port}")
        print_info(f"Database: {database}")
        print_info(f"User: {user}")
        
        # Try to connect
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        # Test query
        result = await conn.fetchval("SELECT 1")
        if result == 1:
            print_success("Database connection successful")
        
        # Check tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        if tables:
            print_success(f"Found {len(tables)} tables:")
            for table in tables:
                print_info(f"  - {table['table_name']}")
        else:
            print_warning("No tables found. Run database migrations.")
        
        await conn.close()
        return True
        
    except Exception as e:
        print_error(f"Database connection failed: {str(e)}")
        return False

def test_model():
    """Test model file and loading"""
    print_header("Testing AI Model")
    
    model_path = os.getenv("MODEL_PATH", "/root/openhermes_backend/openhermes-2.5-mistral-7b.Q4_K_M.gguf")
    print_info(f"Model path: {model_path}")
    
    if os.path.exists(model_path):
        size_gb = os.path.getsize(model_path) / (1024**3)
        print_success(f"Model file found ({size_gb:.2f} GB)")
        
        # Try to import llama-cpp
        try:
            import llama_cpp
            print_success("llama-cpp-python installed")
            
            # Try to load a small test
            print_info("Testing model loading (this may take a moment)...")
            try:
                from app.services.llm_service import llm_service
                llm_service.model_path = model_path
                llm_service.load_model()
                print_success("Model loaded successfully")
                
                # Test generation
                print_info("Testing model generation...")
                response = llm_service.generate("Hello, how are you?", max_tokens=20)
                print_success(f"Model response: {response[:50]}...")
                return True
            except Exception as e:
                print_error(f"Model loading failed: {str(e)}")
                return False
                
        except ImportError:
            print_error("llama-cpp-python not installed")
            print_info("Install with: pip install llama-cpp-python")
            return False
    else:
        print_error(f"Model file not found at {model_path}")
        print_info("Download the model or update MODEL_PATH in .env")
        return False

def test_dependencies():
    """Test Python dependencies"""
    print_header("Testing Dependencies")
    
    required_packages = [
        ("fastapi", "FastAPI web framework"),
        ("uvicorn", "ASGI server"),
        ("asyncpg", "PostgreSQL driver"),
        ("pydantic", "Data validation"),
        ("python-jose", "JWT tokens"),
        ("passlib", "Password hashing"),
        ("python-dotenv", "Environment variables"),
        ("llama_cpp", "LLM inference"),
    ]
    
    missing = []
    for package, description in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print_success(f"{package} - {description}")
        except ImportError:
            print_error(f"{package} - {description} (NOT INSTALLED)")
            missing.append(package)
    
    if missing:
        print_warning(f"\nMissing packages: {', '.join(missing)}")
        print_info("Install with: pip install -r requirements.txt")
        return False
    return True

def test_environment():
    """Test environment variables"""
    print_header("Testing Environment Configuration")
    
    if os.path.exists(".env"):
        print_success(".env file found")
    else:
        print_warning(".env file not found")
        print_info("Copy .env.example to .env and update values")
        return False
    
    required_vars = [
        "POSTGRES_HOST",
        "POSTGRES_PORT", 
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "JWT_SECRET",
        "MODEL_PATH",
    ]
    
    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == "POSTGRES_PASSWORD" or var == "JWT_SECRET":
                print_success(f"{var} = ***hidden***")
            else:
                print_success(f"{var} = {value}")
        else:
            print_error(f"{var} not set")
            missing.append(var)
    
    if missing:
        print_warning(f"\nMissing variables: {', '.join(missing)}")
        return False
    return True

def test_api_structure():
    """Test API structure"""
    print_header("Testing API Structure")
    
    required_files = [
        ("app/__init__.py", "App package"),
        ("app/main.py", "Main FastAPI app"),
        ("app/core/config.py", "Configuration"),
        ("app/core/database.py", "Database connection"),
        ("app/api/v1/routers/auth_router.py", "Auth endpoints"),
        ("app/api/v1/routers/chat_router.py", "Chat endpoints"),
        ("app/services/llm_service.py", "LLM service"),
        ("app/models/auth.py", "Auth models"),
        ("app/models/chat.py", "Chat models"),
    ]
    
    all_exist = True
    for filepath, description in required_files:
        if os.path.exists(filepath):
            print_success(f"{description} ({filepath})")
        else:
            print_error(f"{description} ({filepath}) NOT FOUND")
            all_exist = False
    
    return all_exist

async def test_api_startup():
    """Test if API can start"""
    print_header("Testing API Startup")
    
    try:
        from app.main import app
        from app.core.database import db
        from app.core.config import settings
        
        print_success("FastAPI app imported")
        print_info(f"API will run on {settings.api_host}:{settings.api_port}")
        print_info(f"CORS origins: {settings.cors_origins}")
        
        # Test database connection through the app
        try:
            await db.connect()
            print_success("Database pool created")
            await db.disconnect()
        except Exception as e:
            print_error(f"Database pool failed: {str(e)}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"API startup test failed: {str(e)}")
        return False

async def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*50}{NC}")
    print(f"{BLUE}     Sarah AI System Test Suite{NC}")
    print(f"{BLUE}{'='*50}{NC}")
    
    results = {
        "Environment": test_environment(),
        "Dependencies": test_dependencies(),
        "Database": await test_database(),
        "Model": test_model(),
        "API Structure": test_api_structure(),
        "API Startup": await test_api_startup(),
    }
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        if result:
            print_success(f"{test}: PASSED")
        else:
            print_error(f"{test}: FAILED")
    
    print(f"\n{BLUE}{'='*50}{NC}")
    if passed == total:
        print(f"{GREEN}All tests passed! ({passed}/{total}){NC}")
        print(f"{GREEN}Your system is ready to run.{NC}")
        print(f"\nStart with: {BLUE}python -m app.main{NC}")
    else:
        print(f"{YELLOW}Some tests failed ({passed}/{total}){NC}")
        print(f"{YELLOW}Please fix the issues above before running.{NC}")
    print(f"{BLUE}{'='*50}{NC}\n")
    
    return passed == total

if __name__ == "__main__":
    # Run async main
    success = asyncio.run(main())
    sys.exit(0 if success else 1)