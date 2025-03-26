from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr

class UserSignUp(BaseModel):
    """User signup model"""
    email: EmailStr
    first_name: str
    last_name: str
    company: Optional[str] = None

class RequestLoginCode(BaseModel):
    """Request login code model"""
    email: EmailStr

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

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class LoginResponse(BaseModel):
    """Login response model"""
    message: str
    token: TokenResponse

class LoginRequest(BaseModel):
    """Login request model using email and code"""
    email: EmailStr
    access_code: str
