"""
Authentication service
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
import bcrypt
from jose import JWTError, jwt
from app.core.database import db
from app.models.auth import User, UserRegister, Token
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
    
    @staticmethod
    async def register_user(user_data: UserRegister) -> User:
        """Register a new user"""
        # Check if user exists
        existing = await db.fetchrow(
            "SELECT id FROM users WHERE email = $1 OR username = $2",
            user_data.email, user_data.username
        )
        
        if existing:
            raise ValueError("User with this email or username already exists")
        
        # Create user
        user_id = uuid4()
        hashed_password = AuthService.hash_password(user_data.password)
        
        user = await db.fetchrow("""
            INSERT INTO users (id, email, username, password_hash, full_name, auth_provider)
            VALUES ($1, $2, $3, $4, $5, 'local')
            RETURNING *
        """, user_id, user_data.email, user_data.username, hashed_password, user_data.full_name)
        
        # Create user profile
        await db.execute("""
            INSERT INTO user_profiles (user_id, personality_preference)
            VALUES ($1, 'neutral')
        """, user_id)
        
        return User(**dict(user))
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = await db.fetchrow(
            "SELECT * FROM users WHERE email = $1 AND auth_provider = 'local'",
            email
        )
        
        if not user:
            return None
        
        if not AuthService.verify_password(password, user['password_hash']):
            return None
        
        # Update last login
        await db.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = $1",
            user['id']
        )
        
        return User(**dict(user))
    
    @staticmethod
    async def get_current_user(token: str) -> Optional[User]:
        """Get user from JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None
        except JWTError:
            return None
        
        user = await db.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        if user is None:
            return None
            
        return User(**dict(user))

auth_service = AuthService()
