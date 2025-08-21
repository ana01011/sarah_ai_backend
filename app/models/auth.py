"""
Authentication models with enhanced fields
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from uuid import UUID
from datetime import datetime
from enum import Enum

class GenderType(str, Enum):
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    name: Optional[str] = None  # Made OPTIONAL - will use username if not provided
    gender: Optional[GenderType] = GenderType.NEUTRAL  # Optional with default
    
    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.replace('_', '').isalnum(), 'Username must be alphanumeric (underscores allowed)'
        return v.lower()

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6, max_length=100)

class VerifyEmailRequest(BaseModel):
    token: str

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 86400

class User(BaseModel):
    id: UUID
    email: str
    username: str
    name: Optional[str] = None
    gender: Optional[str] = None
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

class UserProfile(BaseModel):
    id: UUID
    email: str
    username: str
    name: Optional[str]
    gender: Optional[str]
    age: Optional[int]
    location: Optional[str]
    occupation: Optional[str]
    bio: Optional[str]
    relationship_scores: Optional[dict] = {}
    created_at: datetime

class GoogleAuth(BaseModel):
    token: str
    
class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)
