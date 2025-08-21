"""
Authentication models
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    full_name: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleAuth(BaseModel):
    token: str

class User(BaseModel):
    id: UUID
    email: str
    username: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    auth_provider: str
    is_active: bool
    created_at: datetime

class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str]
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    user_id: str
    email: Optional[str] = None
