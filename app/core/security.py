from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings

# Use OAuth2PasswordBearer for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# JWT configuration
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    
    # Use PyJWT for encoding
    try:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    except AttributeError:
        # If jwt.encode is not available, PyJWT might not be installed correctly
        # Try explicit import of PyJWT as a fallback
        import PyJWT
        encoded_jwt = PyJWT.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # In PyJWT 2.0.0+, encode returns a string, not bytes
    if isinstance(encoded_jwt, bytes):
        return encoded_jwt.decode('utf-8')
    
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> Dict[str, Any]:
    """
    Get current user from token
    
    Args:
        token: JWT token from the Authorization header
        
    Returns:
        User information extracted from token
        
    Raises:
        HTTPException: If token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extract user data from payload
        email = payload.get("email")
        if email is None:
            raise credentials_exception
        
        # Return the user data
        return {
            "email": email,
            "first_name": payload.get("first_name"),
            "last_name": payload.get("last_name"),
            "company": payload.get("company")
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise credentials_exception 