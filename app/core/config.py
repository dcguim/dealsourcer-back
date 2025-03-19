import os
from dotenv import load_dotenv
from pydantic import BaseSettings  # Changed from pydantic_settings

# Load .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    # API settings
    API_TITLE: str = "Organization Search API"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"

    # CORS settings
    CORS_ORIGINS: list = ["*"]
    
    # Database settings
    DB_HOST: str = os.getenv("PG_HOST", "localhost")
    DB_PORT: str = os.getenv("PG_PORT", "5432")
    DB_NAME: str = os.getenv("PG_DATABASE", "organization_db")
    DB_USER: str = os.getenv("PG_USER", "orguser")
    DB_PASSWORD: str = os.getenv("PG_PASSWORD", "")
    DB_MIN_CONNECTIONS: int = 5
    DB_MAX_CONNECTIONS: int = 20
    
    # Email settings
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@example.com")
    
    # Auth settings
    ACCESS_CODE_EXPIRY: int = 3600  # 1 hour in seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()
