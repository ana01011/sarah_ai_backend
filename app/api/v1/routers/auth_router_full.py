"""
Enhanced Authentication API routes
"""
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uuid import uuid4
from app.models.auth import (
    UserRegister, UserLogin, Token, User, GoogleAuth, 
    ForgotPasswordRequest, ResetPasswordRequest, UserProfile,
    PasswordChangeRequest, VerifyEmailRequest
)
from app.services.auth.auth_service import auth_service
from app.core.database import db
from app.core.config import settings
from datetime import timedelta
import httpx
from typing import Optional

router = APIRouter()
security = HTTPBearer()

# Define the dependency function FIRST
async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    
    # Decode token
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    # Get user
    user_id = payload.get("sub")
    user = await auth_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

# Now define the routes

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister):
    """Register a new user with name and gender"""
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

@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks
):
    """Request password reset email"""
    reset_token = await auth_service.create_reset_token(request.email)
    
    if reset_token:
        # Send email in background
        background_tasks.add_task(
            auth_service.send_reset_email,
            request.email,
            reset_token
        )
        
        # In development, also return token (remove in production)
        if settings.environment == "development":
            return {
                "message": "Password reset email sent",
                "reset_token": reset_token  # Remove this in production!
            }
    
    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """Reset password with token"""
    success = await auth_service.reset_password(
        request.token,
        request.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )
    
    return {"message": "Password reset successful"}

@router.post("/verify-email")
async def verify_email(request: VerifyEmailRequest):
    """Verify email with token"""
    success = await auth_service.verify_email(request.token)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification token"
        )
    
    return {"message": "Email verified successfully"}

@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user_dependency)
):
    """Change password for logged-in user"""
    # Verify current password
    user = await auth_service.authenticate_user(
        current_user.email,
        request.current_password
    )
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )
    
    # Update to new password
    password_hash = auth_service.hash_password(request.new_password)
    
    await db.execute("""
        UPDATE users 
        SET password_hash = $2, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
    """, current_user.id, password_hash)
    
    return {"message": "Password changed successfully"}

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
            raise HTTPException(status_code=400, detail="Invalid Google token")
        
        google_user = response.json()
        email = google_user.get("email")
        name = google_user.get("name", "")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")
        
        # Check if user exists
        user = await db.fetchrow("""
            SELECT * FROM users WHERE email = $1
        """, email)
        
        if not user:
            # Create new user from Google data
            user_id = uuid4()
            username = email.split('@')[0]  # Use email prefix as username
            
            # Check if username exists and make unique
            counter = 1
            base_username = username
            while await db.fetchval("SELECT 1 FROM users WHERE username = $1", username):
                username = f"{base_username}{counter}"
                counter += 1
            
            user = await db.fetchrow("""
                INSERT INTO users (id, email, username, password_hash, is_verified, created_at)
                VALUES ($1, $2, $3, $4, true, CURRENT_TIMESTAMP)
                RETURNING *
            """, user_id, email, username, "google_oauth_no_password")
            
            # Create profile with Google name
            await db.execute("""
                INSERT INTO user_profiles (user_id, name, created_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
            """, user_id, name)
            
            # Store name as fact
            if name:
                await db.execute("""
                    INSERT INTO user_facts (user_id, fact_type, fact_value, source)
                    VALUES ($1, 'name', $2, 'google_auth')
                    ON CONFLICT DO NOTHING
                """, user_id, name)
        
        # Create token
        access_token = auth_service.create_access_token(
            data={"sub": str(user['id']), "email": user['email']}
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=86400
        )
        
    except httpx.RequestError:
        raise HTTPException(status_code=500, detail="Failed to verify Google token")

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Logout and invalidate session"""
    token = credentials.credentials
    
    # Invalidate session
    await db.execute("""
        UPDATE sessions 
        SET is_active = false 
        WHERE token = $1
    """, token)
    
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserProfile)
async def get_current_user(
    current_user: User = Depends(get_current_user_dependency)
):
    """Get current user profile"""
    profile = await db.fetchrow("""
        SELECT 
            u.id, u.email, u.username, u.created_at,
            p.name, p.gender, p.age, p.location, p.occupation, p.bio
        FROM users u
        LEFT JOIN user_profiles p ON u.id = p.user_id
        WHERE u.id = $1
    """, current_user.id)
    
    # Get relationship scores
    relationships = await db.fetch("""
        SELECT personality, relationship_score
        FROM relationships
        WHERE user_id = $1
    """, current_user.id)
    
    relationship_scores = {r['personality']: r['relationship_score'] for r in relationships}
    
    return UserProfile(
        **dict(profile),
        relationship_scores=relationship_scores
    )
