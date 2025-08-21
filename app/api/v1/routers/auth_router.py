"""
Authentication API routes
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.auth import UserRegister, UserLogin, Token, User, GoogleAuth
from app.services.auth.auth_service import auth_service
from app.core.database import db
from datetime import timedelta
import httpx
from typing import Optional

router = APIRouter()
security = HTTPBearer()

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister):
    """Register a new user"""
    try:
        # Register user
        user = await auth_service.register_user(user_data)
        
        # Create token
        access_token = auth_service.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Store session
        await db.execute("""
            INSERT INTO sessions (user_id, token, expires_at)
            VALUES ($1, $2, CURRENT_TIMESTAMP + INTERVAL '24 hours')
        """, user.id, access_token)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=86400
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login with email and password"""
    user = await auth_service.authenticate_user(user_data.email, user_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create token
    access_token = auth_service.create_access_token(
        data={"sub": str(user.id), "email": user.email}
    )
    
    # Store session
    await db.execute("""
        INSERT INTO sessions (user_id, token, expires_at)
        VALUES ($1, $2, CURRENT_TIMESTAMP + INTERVAL '24 hours')
    """, user.id, access_token)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=86400
    )

@router.post("/google", response_model=Token)
async def google_auth(google_data: GoogleAuth):
    """Authenticate with Google OAuth"""
    try:
        # Verify Google token
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={google_data.token}"
            )
            
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid Google token")
        
        google_user = response.json()
        email = google_user.get("email")
        google_id = google_user.get("sub")
        name = google_user.get("name")
        picture = google_user.get("picture")
        
        # Check if user exists
        user = await db.fetchrow(
            "SELECT * FROM users WHERE email = $1 OR google_id = $2",
            email, google_id
        )
        
        if not user:
            # Create new user
            user = await db.fetchrow("""
                INSERT INTO users (email, google_id, full_name, avatar_url, auth_provider, is_active, is_verified)
                VALUES ($1, $2, $3, $4, 'google', true, true)
                RETURNING *
            """, email, google_id, name, picture)
            
            # Create user profile
            await db.execute("""
                INSERT INTO user_profiles (user_id, name, personality_preference)
                VALUES ($1, $2, 'neutral')
            """, user['id'], name.split()[0] if name else None)
        else:
            # Update user info
            await db.execute("""
                UPDATE users 
                SET full_name = $2, avatar_url = $3, last_login = CURRENT_TIMESTAMP
                WHERE id = $1
            """, user['id'], name, picture)
        
        # Create token
        access_token = auth_service.create_access_token(
            data={"sub": str(user['id']), "email": email}
        )
        
        # Store session
        await db.execute("""
            INSERT INTO sessions (user_id, token, expires_at)
            VALUES ($1, $2, CURRENT_TIMESTAMP + INTERVAL '24 hours')
        """, user['id'], access_token)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=86400
        )
        
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Google OAuth service unavailable")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout and invalidate token"""
    token = credentials.credentials
    
    # Delete session
    await db.execute("DELETE FROM sessions WHERE token = $1", token)
    
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=User)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user info"""
    token = credentials.credentials
    user = await auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return user

async def get_current_user_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current user"""
    token = credentials.credentials
    user = await auth_service.get_current_user(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    return user
