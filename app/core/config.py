"""
Configuration management for Sarah AI
"""
from pydantic_settings import BaseSettings
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "sarah_ai_fresh")
    postgres_user: str = os.getenv("POSTGRES_USER", "sarah_user")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "sarah_secure_2024")
    
    @property
    def database_url(self) -> str:
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    # Security
    jwt_secret: str = os.getenv("JWT_SECRET", "sarah_jwt_secret_2024_secure_key_change_this")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_hours: int = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    
    # Model
    model_path: str = os.getenv("MODEL_PATH", "/root/openhermes_backend/openhermes-2.5-mistral-7b.Q4_K_M.gguf")
    model_context_size: int = int(os.getenv("MODEL_CONTEXT_SIZE", "1024"))
    model_threads: int = int(os.getenv("MODEL_THREADS", "4"))
    model_batch_size: int = int(os.getenv("MODEL_BATCH_SIZE", "256"))
    
    # API
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://147.93.102.165:3001",
        "http://147.93.102.165:3000"
    ]
    
    # Features
    enable_registration: bool = os.getenv("ENABLE_REGISTRATION", "true").lower() == "true"
    enable_google_oauth: bool = os.getenv("ENABLE_GOOGLE_OAUTH", "true").lower() == "true"
    
    # Google OAuth
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    
    # Email settings (for password reset)
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    from_email: str = os.getenv("FROM_EMAIL", "noreply@sarahai.com")
    
    # Frontend URL (for password reset links)
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env

settings = Settings()
