"""
Final working auth router
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.auth import UserRegister, UserLogin, Token, User, GoogleAuth
from app.core.database import db
from app.core.config import settings
from uuid import uuid4
import bcrypt
import jwt
import httpx
from datetime import datetime, timedelta

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
        
        # Create profile
        name = getattr(user_data, 'name', user_data.username)
        gender = getattr(user_data, 'gender', 'neutral')
        
        await db.execute("""
            INSERT INTO user_profiles (user_id, name, gender, created_at)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE SET name = $2, gender = $3
        """, user_id, name, gender)
        
        # Store facts for AI memory
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
        
        # Set AI preference based on gender
        personality = 'sarah' if gender == 'male' else 'xhash' if gender == 'female' else 'neutral'
        await db.execute("""
            UPDATE user_profiles SET personality_preference = $2 WHERE user_id = $1
        """, user_id, personality)
        
        # Create token
        access_token = create_access_token(
            {"sub": str(user_id), "email": user_data.email}
        )
        
        return Token(access_token=access_token)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login user"""
    user = await db.fetchrow(
        "SELECT * FROM users WHERE email = $1",
        user_data.email
    )
    
    if not user or not verify_password(user_data.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    await db.execute("""
        UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1
    """, user['id'])
    
    access_token = create_access_token(
        {"sub": str(user['id']), "email": user['email']}
    )
    
    return Token(access_token=access_token)

@router.post("/google", response_model=Token)
async def google_auth(google_data: GoogleAuth):
    """Google OAuth authentication"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={google_data.token}"
            )
            
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid Google token")
        
        google_user = response.json()
        
        if google_user.get('aud') != settings.google_client_id:
            raise HTTPException(status_code=400, detail="Invalid token audience")
        
        email = google_user.get("email")
        name = google_user.get("name", "")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided")
        
        # Check/create user
        user = await db.fetchrow("SELECT * FROM users WHERE email = $1", email)
        
        if not user:
            user_id = uuid4()
            username = email.split('@')[0]
            
            # Make unique username
            counter = 1
            while await db.fetchval("SELECT 1 FROM users WHERE username = $1", username):
                username = f"{username}{counter}"
                counter += 1
            
            user = await db.fetchrow("""
                INSERT INTO users (id, email, username, password_hash, is_verified, created_at)
                VALUES ($1, $2, $3, 'google_oauth', true, CURRENT_TIMESTAMP)
                RETURNING *
            """, user_id, email, username)
            
            await db.execute("""
                INSERT INTO user_profiles (user_id, name, created_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET name = $2
            """, user_id, name if name else username)
        
        access_token = create_access_token(
            {"sub": str(user['id']), "email": user['email']}
        )
        
        return Token(access_token=access_token)
        
    except Exception as e:
        print(f"Google auth error: {e}")
        raise HTTPException(status_code=500, detail="Google authentication failed")

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
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    raise HTTPException(status_code=401, detail="Could not validate credentials")

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user_dependency)):
    """Get current user info"""
    return current_user

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user"""
    return {"message": "Logged out successfully"}
