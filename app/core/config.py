import os
import secrets
from typing import List
from pydantic import BaseSettings, validator

# Helper function to read from environment with fallbacks
def get_env_value(key, default=None, env_mapping=None):
    if env_mapping and key in env_mapping:
        alt_key = env_mapping[key]
        return os.getenv(alt_key, os.getenv(key, default))
    return os.getenv(key, default)

# Environment variable mapping
ENV_MAPPING = {
    "DB_HOST": "PG_HOST",
    "DB_PORT": "PG_PORT",
    "DB_NAME": "PG_DATABASE",
    "DB_USER": "PG_USER",
    "DB_PASSWORD": "PG_PASSWORD",
    "EMAIL_HOST": "SMTP_HOST",
    "EMAIL_PORT": "SMTP_PORT",
    "EMAIL_USER": "SMTP_USERNAME",
    "EMAIL_PASSWORD": "SMTP_PASSWORD"
}

class Settings(BaseSettings):
    # API settings
    API_TITLE: str
    API_VERSION: str
    DEBUG: bool
    
    # Database settings - using direct variables from .env
    DB_HOST: str
    DB_PORT: int
    DB_DATABASE: str
    DB_USER: str
    DB_PASSWORD: str
    DB_MIN_CONNECTIONS: int
    DB_MAX_CONNECTIONS: int
    
    # Property to map DB_DATABASE to DB_NAME for consistency in code
    @property
    def DB_NAME(self):
        return self.DB_DATABASE
    
    # CORS settings
    CORS_ORIGINS: List[str]
    
    # JWT Authentication settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # Email verification settings
    ACCESS_CODE_EXPIRY: int
    
    # Email settings - using environment variable names from .env
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    EMAIL_FROM: str
    EMAIL_USE_TLS: bool
    
    # Properties to map SMTP_* to EMAIL_* for consistency in code
    @property
    def EMAIL_HOST(self):
        return self.SMTP_HOST
        
    @property
    def EMAIL_PORT(self):
        return self.SMTP_PORT
        
    @property
    def EMAIL_USER(self):
        return self.SMTP_USERNAME
        
    @property
    def EMAIL_PASSWORD(self):
        return self.SMTP_PASSWORD
    
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except:
                return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Safety check for production
if not settings.DEBUG and settings.SECRET_KEY == "":
    raise ValueError("SECRET_KEY must be set in production mode")
