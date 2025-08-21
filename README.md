# Sarah AI Backend
# Sarah AI Backend - OpenHermes Powered Chat System

## 🚀 Overview

This is a sophisticated AI chat backend system built with FastAPI and powered by OpenHermes 2.5 Mistral 7B model. The system features multiple AI personalities (Sarah, Xhash, and Neutral) with advanced relationship-building capabilities, user memory, and context-aware responses.

## 🏗️ Architecture

### Core Components

#### 1. **FastAPI Application** (`app/`)
- **Main Entry Point**: `app/main.py` - FastAPI application with CORS, lifespan management
- **API Version**: v1 with modular router system
- **Port**: 8000 (configurable via environment)

#### 2. **AI Personalities System** (`app/agents/`)
- **Sarah**: Female persona for male users - warm, empathetic, flirty
- **Xhash**: Male persona for female users - confident, charming
- **Neutral**: Default persona when gender is unknown
- **Base Agent**: Abstract base class for all personalities
- **Intent Router**: Routes messages to appropriate handlers
- **Memory Manager**: Manages conversation context and user memory

#### 3. **API Endpoints** (`app/api/v1/routers/`)
- **Authentication** (`/api/v1/auth/`)
  - `/register` - User registration
  - `/login` - User login
  - `/google` - Google OAuth
  - `/logout` - Session termination
  - `/me` - Current user info

- **Chat** (`/api/v1/chat/`)
  - `/chat` - Main chat endpoint
  - `/conversations` - Get user conversations
  - `/conversations/{id}` - Get specific conversation
  - `/conversations/{id}/messages` - Get conversation messages

- **Users** (`/api/v1/users/`)
  - `/profile` - Get/update user profile
  - `/preferences` - User preferences management

#### 4. **Database Layer** (`app/database/`)
- **PostgreSQL** with asyncpg
- **Connection Pooling**: 5-20 connections
- **Tables**:
  - `users` - User accounts
  - `user_profiles` - Extended user information
  - `conversations` - Chat sessions
  - `messages` - Chat messages
  - `user_facts` - Extracted user information
  - `sessions` - Active user sessions

#### 5. **Services** (`app/services/`)
- **LLM Service**: Manages OpenHermes model loading and inference
- **Auth Service**: JWT authentication, password hashing
- **Chat Service**: Message processing, context management
- **Memory Service**: User memory and fact extraction
- **User Service**: User profile management

#### 6. **Models** (`app/models/`)
- **Pydantic Models** for:
  - Authentication (User, Token, UserRegister, UserLogin)
  - Chat (ChatMessage, ChatResponse, Conversation, Message)
  - User profiles and preferences

#### 7. **Relationship System** (`relationship_system.py`)
- **Gender Detection**: Automatic from conversation
- **Relationship Stages**: 
  - Stranger (0-10)
  - Acquaintance (11-25)
  - Friend (26-45)
  - Close Friend (46-65)
  - Romantic Interest (66-85)
  - Partner (86-100)
- **Dynamic Responses**: Based on relationship level
- **User Memory**: Persistent across sessions

## 📁 Repository Structure

```
openhermes_backend/
├── app/                          # Main application
│   ├── main.py                  # FastAPI entry point
│   ├── agents/                  # AI agents and personalities
│   │   ├── personalities/       # Sarah, Xhash, Neutral
│   │   ├── base/               # Base agent classes
│   │   └── executives/         # Intent routing, memory
│   ├── api/                    # API endpoints
│   │   └── v1/
│   │       └── routers/        # Auth, Chat, User routes
│   ├── core/                   # Core utilities
│   │   ├── config.py          # Settings management
│   │   └── database.py        # Database connection
│   ├── database/              # Database layer
│   │   ├── migrations/        # DB migrations
│   │   └── repositories/      # Data access layer
│   ├── models/                # Pydantic models
│   ├── services/              # Business logic
│   └── utils/                 # Utility functions
│
├── old_versions/              # Previous iterations
├── backups/                   # Backup files
├── .github/                   # GitHub workflows
│
├── relationship_system.py     # Relationship AI logic
├── user_memory.json          # User memory storage
├── relationship_profiles.json # Relationship data
├── requirements.txt          # Python dependencies
├── production_config.md      # Production settings
└── scripts/                  # Utility scripts
    ├── start.sh
    ├── start_production.sh
    └── setup_agents.sh
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- 8GB+ RAM (for model)
- OpenHermes 2.5 Mistral 7B model file

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd openhermes_backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the root directory:

```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=sarah_ai_fresh
POSTGRES_USER=sarah_user
POSTGRES_PASSWORD=sarah_secure_2024
# Security
JWT_SECRET=your_secure_jwt_secret_key_change_this
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
# Model
MODEL_PATH=/path/to/openhermes-2.5-mistral-7b.Q4_K_M.gguf
MODEL_CONTEXT_SIZE=1024
MODEL_THREADS=4
MODEL_BATCH_SIZE=256
# API
API_HOST=0.0.0.0
API_PORT=8000
# Google OAuth (optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
# Features
ENABLE_REGISTRATION=true
ENABLE_GOOGLE_OAUTH=true
LOG_LEVEL=INFO
```

### 5. Set Up Database
```bash
# Create database
createdb sarah_ai_fresh

# Run migrations (if available)
# python -m app.database.migrations
```

### 6. Download Model
Download the OpenHermes 2.5 Mistral 7B Q4_K_M model and place it in the path specified in MODEL_PATH.

## 🚀 Running the Application

### Development Mode
```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the module
python -m app.main
```

### Production Mode
```bash
# Using the production script
./start_production.sh

# Or with optimal settings
taskset -c 4-7 nice -n -20 uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

## 🔍 Fixing Common Issues

### Port 8000 Already in Use
```bash
# Kill any processes using port 8000
pkill -f "python.*main"
pkill -f uvicorn

# Or find and kill specific process
fuser -k 8000/tcp
```

### Model Loading Issues
- Ensure model file exists at specified path
- Check available RAM (needs ~4-6GB)
- Verify model file integrity

### Database Connection Issues
- Check PostgreSQL is running
- Verify credentials in .env
- Ensure database exists

## 📊 Performance Optimization

Based on production testing:
- **CPU Cores**: 4-7 dedicated to model
- **Threads**: 4 (matches core count)
- **Batch Size**: 256
- **Context Size**: 1024
- **Average Speed**: 15-17 tokens/second

## 🔒 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Session management
- CORS configuration
- Input validation with Pydantic
- SQL injection prevention with parameterized queries

## 📝 API Documentation

Once running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🧪 Testing

```bash
# Quick test
python quick_test.py

# Test scenarios
./test_scenarios.sh

# Memory test
./test_fixed_memory.sh
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## 📄 License

[Your License Here]

## 👥 Contact

[Your Contact Information]

---

**Note**: This is an AI-powered chat system with personality adaptation and relationship building. The system learns from conversations and adapts responses based on user interaction patterns.
