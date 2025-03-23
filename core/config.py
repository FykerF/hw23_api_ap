import os
from typing import List
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "URL Shortener"
    DEBUG: bool = False
    SECRET_KEY: str
    DOMAIN: str
    PROTOCOL: str = "http"
    
    # Database connection
    DATABASE_URL: str
    
    # Redis cache connection
    REDIS_URL: str
    
    # JWT settings
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Shortcode settings
    SHORTCODE_LENGTH: int = 6
    ALLOW_CUSTOM_ALIASES: bool = True
    
    # Link cleanup settings
    CLEANUP_UNUSED_LINKS_DAYS: int = 90
    CLEANUP_JOB_INTERVAL_HOURS: int = 24
    
    # Security settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    RATE_LIMIT_PER_MINUTE: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Load settings from environment variables
settings = Settings()

# Helper function to get the base URL
def get_base_url() -> str:
    return f"{settings.PROTOCOL}://{settings.DOMAIN}"