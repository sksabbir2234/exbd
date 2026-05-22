from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # App
    APP_NAME: str = "Exam Prep BD"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/exam_prep_bd"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://examprepbd.com",
    ]
    
    # Storage (Cloudflare R2)
    R2_BUCKET_NAME: Optional[str] = None
    R2_ACCOUNT_ID: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_PUBLIC_URL: Optional[str] = None
    
    # Email (Resend)
    RESEND_API_KEY: Optional[str] = None
    FROM_EMAIL: str = "noreply@examprepbd.com"
    
    # Payment (SSLCommerz)
    SSL_STORE_ID: Optional[str] = None
    SSL_STORE_PASSWORD: Optional[str] = None
    SSL_PAYMENT_URL: str = "https://sandbox.sslcommerz.com/gwprocess/v3/api.json"
    
    # AI (Groq)
    GROQ_API_KEY: Optional[str] = None
    
    # Redis (Upstash)
    REDIS_URL: Optional[str] = None
    
    # Scheduler
    SCRAPE_INTERVAL_HOURS: int = 6
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
