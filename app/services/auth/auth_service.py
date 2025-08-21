"""
Authentication service with OTP support
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
import bcrypt
from jose import JWTError, jwt
from app.core.database import db
from app.models.auth import User, UserRegister, Token
from app.services.email_service import email_service
import os

SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-this")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password"""
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    async def register_user(self, user_data: UserRegister) -> dict:
        """Register a new user with email verification"""
        # Check if user exists
        existing_user = await db.fetchrow("""
            SELECT id FROM users 
            WHERE email = $1 OR username = $2
        """, user_data.email, user_data.username)
        
        if existing_user:
            raise ValueError("User with this email or username already exists")
        
        # Create user (NOT verified by default)
        user_id = uuid4()
        password_hash = self.hash_password(user_data.password)
        
        await db.execute("""
            INSERT INTO users (
                id, email, username, password_hash, 
                is_verified, created_at
            ) VALUES ($1, $2, $3, $4, false, CURRENT_TIMESTAMP)
        """, user_id, user_data.email, user_data.username, password_hash)
        
        # Create user profile
        name = getattr(user_data, 'name', user_data.username)
        gender = getattr(user_data, 'gender', 'neutral')
        
        await db.execute("""
            INSERT INTO user_profiles (
                user_id, name, gender, created_at
            ) VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE 
            SET name = $2, gender = $3
        """, user_id, name, gender)
        
        # Store initial facts
        if name:
            await db.execute("""
                INSERT INTO user_facts (user_id, fact_type, fact_value, source)
                VALUES ($1, 'name', $2, 'registration')
                ON CONFLICT DO NOTHING
            """, user_id, name)
        
        if gender:
            await db.execute("""
                INSERT INTO user_facts (user_id, fact_type, fact_value, source)
                VALUES ($1, 'gender', $2, 'registration')
                ON CONFLICT DO NOTHING
            """, user_id, gender)
        
        # Set personality preference based on gender
        personality = 'sarah' if gender == 'male' else 'xhash' if gender == 'female' else 'neutral'
        await db.execute("""
            UPDATE user_profiles 
            SET personality_preference = $2 
            WHERE user_id = $1
        """, user_id, personality)
        
        # Send verification OTP
        otp = await email_service.send_verification_otp(str(user_id), user_data.email)
        
        return {
            "id": str(user_id),
            "email": user_data.email,
            "username": user_data.username,
            "is_verified": False,
            "message": "Registration successful! Please check your email for verification code."
        }
    
    async def verify_otp(self, email: str, otp: str) -> dict:
        """Verify OTP for email verification"""
        user = await db.fetchrow("""
            SELECT id, verification_otp, otp_expires_at, otp_attempts, is_verified
            FROM users WHERE email = $1
        """, email)
        
        if not user:
            raise ValueError("User not found")
        
        if user['is_verified']:
            raise ValueError("Email already verified")
        
        # Check OTP attempts
        if user['otp_attempts'] >= 3:
            raise ValueError("Too many failed attempts. Please request a new OTP.")
        
        # Check OTP expiry
        if user['otp_expires_at'] and datetime.utcnow() > user['otp_expires_at']:
            raise ValueError("OTP expired. Please request a new one.")
        
        # Verify OTP
        if user['verification_otp'] != otp:
            # Increment attempts
            await db.execute("""
                UPDATE users 
                SET otp_attempts = otp_attempts + 1 
                WHERE id = $1
            """, user['id'])
            raise ValueError("Invalid OTP")
        
        # Mark as verified
        await db.execute("""
            UPDATE users 
            SET is_verified = true,
                verification_otp = NULL,
                otp_expires_at = NULL,
                otp_attempts = 0
            WHERE id = $1
        """, user['id'])
        
        # Send welcome email
        profile = await db.fetchrow("""
            SELECT name FROM user_profiles WHERE user_id = $1
        """, user['id'])
        
        name = profile['name'] if profile else email.split('@')[0]
        await email_service.send_email(
            email,
            "Welcome to Sarah AI! 🎊",
            f"Hi {name}! Your email has been verified. You can now login and start chatting!",
            is_html=False
        )
        
        # Create access token
        access_token = self.create_access_token(
            data={"sub": str(user['id']), "email": email}
        )
        
        return {
            "access_token": access_token,
            "message": "Email verified successfully!"
        }
    
    async def resend_otp(self, email: str) -> dict:
        """Resend verification OTP"""
        user = await db.fetchrow("""
            SELECT id, is_verified FROM users WHERE email = $1
        """, email)
        
        if not user:
            raise ValueError("User not found")
        
        if user['is_verified']:
            raise ValueError("Email already verified")
        
        # Send new OTP
        await email_service.send_verification_otp(str(user['id']), email)
        
        return {"message": "New verification code sent to your email"}
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user - requires verification"""
        user = await db.fetchrow("""
            SELECT * FROM users WHERE email = $1
        """, email)
        
        if not user:
            return None
        
        # Check if email is verified
        if not user['is_verified']:
            raise ValueError("Please verify your email first. Check your inbox for the verification code.")
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            return None
        
        # Update last login
        await db.execute("""
            UPDATE users 
            SET last_login = CURRENT_TIMESTAMP,
                login_count = COALESCE(login_count, 0) + 1
            WHERE id = $1
        """, user['id'])
        
        return User(**dict(user))
    
    async def login_with_2fa(self, email: str, password: str) -> dict:
        """Login with 2FA - sends OTP"""
        user = await db.fetchrow("""
            SELECT * FROM users WHERE email = $1
        """, email)
        
        if not user:
            raise ValueError("Invalid credentials")
        
        if not user['is_verified']:
            raise ValueError("Please verify your email first")
        
        if not self.verify_password(password, user['password_hash']):
            raise ValueError("Invalid credentials")
        
        # Send login OTP
        await email_service.send_login_otp(email)
        
        return {
            "message": "Login code sent to your email",
            "require_otp": True
        }
    
    async def verify_login_otp(self, email: str, otp: str) -> dict:
        """Verify login OTP and return token"""
        user = await db.fetchrow("""
            SELECT id, login_otp, login_otp_expires
            FROM users WHERE email = $1
        """, email)
        
        if not user:
            raise ValueError("User not found")
        
        # Check OTP expiry
        if user['login_otp_expires'] and datetime.utcnow() > user['login_otp_expires']:
            raise ValueError("OTP expired")
        
        # Verify OTP
        if user['login_otp'] != otp:
            raise ValueError("Invalid OTP")
        
        # Clear OTP
        await db.execute("""
            UPDATE users 
            SET login_otp = NULL,
                login_otp_expires = NULL,
                last_login = CURRENT_TIMESTAMP
            WHERE id = $1
        """, user['id'])
        
        # Create token
        access_token = self.create_access_token(
            data={"sub": str(user['id']), "email": email}
        )
        
        return {"access_token": access_token}
    
    async def reset_password_with_otp(self, email: str, otp: str, new_password: str) -> dict:
        """Reset password using OTP"""
        user = await db.fetchrow("""
            SELECT id, reset_otp, reset_otp_expires
            FROM users WHERE email = $1
        """, email)
        
        if not user:
            raise ValueError("User not found")
        
        # Check OTP expiry
        if user['reset_otp_expires'] and datetime.utcnow() > user['reset_otp_expires']:
            raise ValueError("OTP expired")
        
        # Verify OTP
        if user['reset_otp'] != otp:
            raise ValueError("Invalid OTP")
        
        # Update password
        password_hash = self.hash_password(new_password)
        await db.execute("""
            UPDATE users 
            SET password_hash = $2,
                reset_otp = NULL,
                reset_otp_expires = NULL
            WHERE id = $1
        """, user['id'], password_hash)
        
        return {"message": "Password reset successfully"}

# Singleton instance
auth_service = AuthService()
