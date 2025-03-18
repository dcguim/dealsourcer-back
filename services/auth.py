import secrets
import time
from typing import Dict, Optional, Any, Tuple
from app.models.auth import UserSignUp, AccessCodeData
from app.core.email import send_email
from app.core.config import settings

# In-memory store for access codes (replace with database in production)
access_codes: Dict[str, AccessCodeData] = {}

async def create_access_code(user: UserSignUp) -> str:
    """
    Create and store an access code for user signup
    
    Args:
        user: User signup information
        
    Returns:
        Generated access code
    """
    # Generate a 6-character access code
    access_code = secrets.token_hex(3).upper()  # 6 characters
    
    # Store the code with expiration
    access_codes[user.email] = AccessCodeData(
        code=access_code,
        user_info=user.dict(),
        expiry_seconds=settings.ACCESS_CODE_EXPIRY
    )
    
    return access_code

async def send_verification_email(user: UserSignUp, access_code: str) -> bool:
    """
    Send verification email with access code
    
    Args:
        user: User information
        access_code: Generated access code
        
    Returns:
        True if email sent successfully, False otherwise
    """
    subject = "Your Access Code for Organization Search"
    
    text_content = f"""
    Hello {user.first_name},
    
    Thank you for signing up for Organization Search. Your access code is:
    
    {access_code}
    
    This code will expire in 1 hour.
    
    Best regards,
    The Organization Search Team
    """
    
    html_content = f"""
    <html>
    <body>
        <p>Hello {user.first_name},</p>
        <p>Thank you for signing up for Organization Search. Your access code is:</p>
        <h2 style="background-color: #f0f0f0; padding: 10px; font-family: monospace; text-align: center;">{access_code}</h2>
        <p>This code will expire in 1 hour.</p>
        <p>Best regards,<br>The Organization Search Team</p>
    </body>
    </html>
    """
    
    return await send_email(user.email, subject, html_content, text_content)

async def verify_access_code(email: str, code: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Verify an access code
    
    Args:
        email: User email address
        code: Access code to verify
        
    Returns:
        Tuple of (is_valid, user_info)
        - is_valid: True if the code is valid and not expired
        - user_info: User information if the code is valid, None otherwise
    """
    # Check if email exists in our store
    if email not in access_codes:
        return False, None
    
    stored_data = access_codes[email]
    
    # Check if code has expired
    if stored_data.is_expired():
        del access_codes[email]
        return False, None
    
    # Check if code matches
    if not stored_data.matches(code):
        return False, None
    
    # Code is valid, get user info
    user_info = stored_data.user_info
    
    # Clean up the verified code
    del access_codes[email]
    
    return True, user_info
