"""
Debug version of auth router to see actual errors
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.auth import UserRegister, UserLogin, Token, User
from app.core.database import db
from app.core.config import settings
from uuid import uuid4
import bcrypt
import jwt
from datetime import datetime, timedelta
import traceback

router = APIRouter()
security = HTTPBearer()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister):
    """Register with detailed error reporting"""
    try:
        print(f"Registration attempt for: {user_data.email}")
        
        # Check if user exists
        existing = await db.fetchrow(
            "SELECT id FROM users WHERE email = $1 OR username = $2",
            user_data.email, user_data.username
        )
        
        if existing:
            print(f"User already exists: {user_data.email}")
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create user
        user_id = uuid4()
        password_hash = hash_password(user_data.password)
        
        print(f"Creating user with ID: {user_id}")
        
        await db.execute("""
            INSERT INTO users (id, email, username, password_hash, created_at)
            VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
        """, user_id, user_data.email, user_data.username, password_hash)
        
        print(f"User created, creating profile...")
        
        # Create profile
        name = getattr(user_data, 'name', user_data.username)
        gender = getattr(user_data, 'gender', 'neutral')
        
        await db.execute("""
            INSERT INTO user_profiles (user_id, name, gender, created_at)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET name = $2, gender = $3
        """, user_id, name, gender)
        
        print(f"Profile created, storing facts...")
        
        # Store facts
        await db.execute("""
            INSERT INTO user_facts (user_id, fact_type, fact_value, source)
            VALUES ($1, 'name', $2, 'registration')
            ON CONFLICT DO NOTHING
        """, user_id, name)
        
        await db.execute("""
            INSERT INTO user_facts (user_id, fact_type, fact_value, source)
            VALUES ($1, 'gender', $2, 'registration')
            ON CONFLICT DO NOTHING
        """, user_id, gender)
        
        print(f"Facts stored, creating token...")
        
        # Create token
        access_token = create_access_token(
            {"sub": str(user_id), "email": user_data.email}
        )
        
        print(f"Registration successful for: {user_data.email}")
        
        return Token(access_token=access_token)
        
    except HTTPException as he:
        print(f"HTTP Exception: {he.detail}")
        raise
    except Exception as e:
        error_msg = f"Registration failed: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        # Return the actual error for debugging
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login user"""
    try:
        user = await db.fetchrow(
            "SELECT * FROM users WHERE email = $1",
            user_data.email
        )
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
            
        if not verify_password(user_data.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid password")
        
        access_token = create_access_token(
            {"sub": str(user['id']), "email": user['email']}
        )
        
        return Token(access_token=access_token)
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current user from token"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        
        user = await db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        if user:
            return User(**dict(user))
    except:
        pass
    
    raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user_dependency)):
    """Get current user"""
    return current_user
