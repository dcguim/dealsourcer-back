from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr
import time

class UserSignUp(BaseModel):
    """User signup model"""
    email: EmailStr
    first_name: str
    last_name: str
    company: Optional[str] = None

class VerifyCode(BaseModel):
    """Code verification model"""
    email: EmailStr
    access_code: str

class UserResponse(BaseModel):
    """User response model"""
    email: EmailStr
    first_name: str
    last_name: str
    company: Optional[str] = None

class AccessCodeData:
    """Access code data - used internally"""
    def __init__(self, code: str, user_info: Dict[str, Any], expiry_seconds: int = 3600):
        self.code = code
        self.user_info = user_info
        self.expires_at = time.time() + expiry_seconds
    
    def is_expired(self) -> bool:
        """Check if the access code has expired"""
        return time.time() > self.expires_at
    
    def matches(self, code: str) -> bool:
        """Check if the provided code matches"""
        return self.code == code
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "code": self.code,
            "user_info": self.user_info,
            "expires_at": self.expires_at
        }
