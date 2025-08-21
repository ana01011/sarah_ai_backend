"""
Simple working auth router
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.auth import UserRegister, UserLogin, Token, User
from app.core.database import db
from uuid import uuid4
import bcrypt
import jwt
from datetime import datetime, timedelta
from app.core.config import settings

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
    """Register a new user"""
    try:
        # Check if user exists
        existing = await db.fetchrow(
            "SELECT id FROM users WHERE email = $1 OR username = $2",
            user_data.email, user_data.username
        )
        
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create user
        user_id = uuid4()
        password_hash = hash_password(user_data.password)
        
        await db.execute("""
            INSERT INTO users (id, email, username, password_hash, created_at)
            VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
        """, user_id, user_data.email, user_data.username, password_hash)
        
        # Create profile with name and gender if provided
        name = getattr(user_data, 'name', user_data.username)
        gender = getattr(user_data, 'gender', 'neutral')
        
        await db.execute("""
            INSERT INTO user_profiles (user_id, name, gender, created_at)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET name = $2, gender = $3
        """, user_id, name, gender)
        
        # Create token
        access_token = create_access_token(
            {"sub": str(user_id), "email": user_data.email}
        )
        
        return Token(access_token=access_token)
        
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login user"""
    user = await db.fetchrow(
        "SELECT * FROM users WHERE email = $1",
        user_data.email
    )
    
    if not user or not verify_password(user_data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(
        {"sub": str(user['id']), "email": user['email']}
    )
    
    return Token(access_token=access_token)

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
