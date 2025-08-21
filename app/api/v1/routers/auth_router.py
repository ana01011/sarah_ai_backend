"""
Authentication API routes with OTP
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from app.models.auth import UserRegister, UserLogin, Token, User, GoogleAuth
from app.services.auth.auth_service import auth_service
from app.core.database import db
from app.core.config import settings
from jose import jwt, JWTError
import httpx
from typing import Optional

router = APIRouter()
security = HTTPBearer()

# OTP Models
class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ResendOTPRequest(BaseModel):
    email: EmailStr

class LoginOTPRequest(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordOTPRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str

@router.post("/register")
async def register(user_data: UserRegister):
    """Register a new user - sends verification OTP"""
    try:
        result = await auth_service.register_user(user_data)
        return {
            "message": result["message"],
            "email": result["email"],
            "is_verified": result["is_verified"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/verify-otp", response_model=Token)
async def verify_otp(request: VerifyOTPRequest):
    """Verify OTP and complete registration"""
    try:
        result = await auth_service.verify_otp(request.email, request.otp)
        return Token(
            access_token=result["access_token"],
            token_type="bearer"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"OTP verification error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")

@router.post("/resend-otp")
async def resend_otp(request: ResendOTPRequest):
    """Resend verification OTP"""
    try:
        result = await auth_service.resend_otp(request.email)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Resend OTP error: {e}")
        raise HTTPException(status_code=500, detail="Failed to resend OTP")

@router.post("/login")
async def login(user_data: UserLogin):
    """Login user - checks if verified"""
    try:
        # Check if 2FA is enabled
        user_record = await db.fetchrow("""
            SELECT require_2fa FROM users WHERE email = $1
        """, user_data.email)
        
        if user_record and user_record['require_2fa']:
            # Send OTP for 2FA
            result = await auth_service.login_with_2fa(user_data.email, user_data.password)
            return result
        else:
            # Normal login
            user = await auth_service.authenticate_user(user_data.email, user_data.password)
            if not user:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            access_token = auth_service.create_access_token(
                data={"sub": str(user.id), "email": user.email}
            )
            
            return Token(
                access_token=access_token,
                token_type="bearer"
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/login-verify-otp", response_model=Token)
async def verify_login_otp(request: LoginOTPRequest):
    """Verify login OTP for 2FA"""
    try:
        result = await auth_service.verify_login_otp(request.email, request.otp)
        return Token(
            access_token=result["access_token"],
            token_type="bearer"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Login OTP error: {e}")
        raise HTTPException(status_code=500, detail="Verification failed")

@router.post("/forgot-password")
async def forgot_password(request: ResendOTPRequest):
    """Send password reset OTP"""
    try:
        from app.services.email_service import email_service
        success = await email_service.send_password_reset_otp(request.email)
        if success:
            return {"message": "Password reset code sent to your email"}
        else:
            raise HTTPException(status_code=404, detail="Email not found")
    except Exception as e:
        print(f"Forgot password error: {e}")
        raise HTTPException(status_code=500, detail="Failed to send reset code")

@router.post("/reset-password-otp")
async def reset_password_with_otp(request: ResetPasswordOTPRequest):
    """Reset password using OTP"""
    try:
        result = await auth_service.reset_password_with_otp(
            request.email, request.otp, request.new_password
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Password reset error: {e}")
        raise HTTPException(status_code=500, detail="Password reset failed")

async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current user from token"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret, 
            algorithms=[settings.jwt_algorithm]
        )
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = await db.fetchrow("""
            SELECT * FROM users WHERE id = $1 AND is_verified = true
        """, user_id)
        
        if not user:
            raise HTTPException(status_code=401, detail="User not found or not verified")
        
        return User(**dict(user))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user_dependency)):
    """Get current user info"""
    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user_dependency)):
    """Logout user"""
    # You can add token blacklisting here if needed
    return {"message": "Logged out successfully"}

@router.post("/enable-2fa")
async def enable_2fa(current_user: User = Depends(get_current_user_dependency)):
    """Enable 2FA for user"""
    await db.execute("""
        UPDATE users SET require_2fa = true WHERE id = $1
    """, current_user.id)
    return {"message": "2FA enabled successfully"}

@router.post("/disable-2fa")
async def disable_2fa(current_user: User = Depends(get_current_user_dependency)):
    """Disable 2FA for user"""
    await db.execute("""
        UPDATE users SET require_2fa = false WHERE id = $1
    """, current_user.id)
    return {"message": "2FA disabled successfully"}

@router.post("/google", response_model=Token)
async def google_auth(google_data: GoogleAuth):
    """Google OAuth authentication - auto-verified"""
    try:
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
            raise HTTPException(status_code=400, detail="Email not provided")
        
        # Check if user exists
        user = await db.fetchrow("SELECT * FROM users WHERE email = $1", email)
        
        if not user:
            # Create new user (auto-verified for Google users)
            from uuid import uuid4
            user_id = uuid4()
            username = email.split('@')[0]
            
            # Ensure unique username
            counter = 1
            while await db.fetchval("SELECT 1 FROM users WHERE username = $1", username):
                username = f"{email.split('@')[0]}{counter}"
                counter += 1
            
            await db.execute("""
                INSERT INTO users (
                    id, email, username, password_hash, 
                    is_verified, created_at
                ) VALUES ($1, $2, $3, 'google_oauth', true, CURRENT_TIMESTAMP)
            """, user_id, email, username)
            
            await db.execute("""
                INSERT INTO user_profiles (user_id, name, created_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET name = $2
            """, user_id, name if name else username)
            
            user = await db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        
        # Create token
        access_token = auth_service.create_access_token(
            data={"sub": str(user['id']), "email": user['email']}
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer"
        )
    except Exception as e:
        print(f"Google auth error: {e}")
        raise HTTPException(status_code=500, detail="Google authentication failed")
