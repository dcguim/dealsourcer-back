import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple
from app.models.auth import UserSignUp, TokenResponse, UserResponse
from app.core.email import send_email
from app.core.config import settings
from app.core.security import create_access_token
import asyncpg
import json

async def create_access_code(pool: asyncpg.Pool, user: UserSignUp) -> str:
    """
    Create and store an access code for user signup in the database
    
    Args:
        pool: Database connection pool
        user: User signup information
        
    Returns:
        Generated access code
    """
    # Generate a 6-character access code
    access_code = secrets.token_hex(3).upper()  # 6 characters
    
    # Calculate expiration time
    expires_at = datetime.now() + timedelta(seconds=settings.ACCESS_CODE_EXPIRY)
    
    async with pool.acquire() as conn:
        # First check if the user already exists
        existing_user = await conn.fetchrow(
            "SELECT id, first_name, last_name, company FROM users WHERE email = $1",
            user.email
        )
        
        if not existing_user:
            # User doesn't exist, we'll create them after verification
            pass
        
        # Store the code in the database
        await conn.execute(
            """
            INSERT INTO access_codes(email, code, user_info, expires_at)
            VALUES($1, $2, $3, $4)
            """,
            user.email,
            access_code,
            json.dumps(user.dict()),
            expires_at
        )
    
    return access_code

async def generate_login_code(pool: asyncpg.Pool, email: str) -> Tuple[bool, str]:
    """
    Generate a login code for an existing user
    
    Args:
        pool: Database connection pool
        email: User email address
        
    Returns:
        Tuple of (success, code or error message)
        - success: True if user exists and code was generated
        - code or error: Access code if successful, error message if not
    """
    async with pool.acquire() as conn:
        # Check if user exists
        user_record = await conn.fetchrow(
            "SELECT email, first_name, last_name, company FROM users WHERE email = $1",
            email
        )
        
        if not user_record:
            return False, "User not found"
        
        # Convert record to a dictionary
        user_info = dict(user_record)
        
        # Generate a 6-character access code
        access_code = secrets.token_hex(3).upper()  # 6 characters
        
        # Calculate expiration time
        expires_at = datetime.now() + timedelta(seconds=settings.ACCESS_CODE_EXPIRY)
        
        # Store the code in the database
        await conn.execute(
            """
            INSERT INTO access_codes(email, code, user_info, expires_at)
            VALUES($1, $2, $3, $4)
            """,
            email,
            access_code,
            json.dumps(user_info),
            expires_at
        )
        
        return True, access_code

async def send_verification_email(user: UserSignUp, access_code: str) -> bool:
    """
    Send verification email with access code
    
    Args:
        user: User information
        access_code: Generated access code
        
    Returns:
        True if email sent successfully, False otherwise
    """
    subject = "Verify Your Deal Sourcer Account"
    
    text_content = f"""
    Hello {user.first_name},
    
    Thank you for signing up for Deal Sourcer. To complete your registration, please use the following verification code:
    
    {access_code}
    
    This code will expire in 1 hour.
    
    Best regards,
    The Deal Sourcer Team
    Berlin, Germany
    """
    
    # Deal Sourcer brand colors
    brand_color = "#3b3992"  # Primary indigo blue
    brand_color_light = "#ecedf7"  # Very light shade for backgrounds
    brand_color_medium = "#9d9ccc"  # Medium shade for accents
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; color: #333333; line-height: 1.6; background-color: #f5f7fa;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <!-- Header with Logo -->
            <div style="background-color: {brand_color}; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">Deal Sourcer</h1>
            </div>
            
            <!-- Main Content -->
            <div style="background-color: #ffffff; padding: 40px 30px; border-left: 1px solid #e5e7eb; border-right: 1px solid #e5e7eb; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                <h2 style="color: {brand_color}; margin-top: 0; font-size: 22px;">Welcome to Deal Sourcer!</h2>
                <p style="margin-bottom: 25px;">Hello {user.first_name},</p>
                <p>Thank you for signing up for Deal Sourcer. To complete your registration, please use the verification code below:</p>
                
                <!-- Code Box -->
                <div style="background-color: {brand_color_light}; border: 2px solid {brand_color}; border-radius: 8px; padding: 20px; margin: 30px 0; text-align: center;">
                    <p style="font-family: 'Courier New', monospace; font-size: 32px; font-weight: bold; letter-spacing: 6px; margin: 0; color: {brand_color};">{access_code}</p>
                </div>
                
                <p>This code will expire in 1 hour.</p>
                <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">If you did not request this verification, please ignore this email.</p>
            </div>
            
            <!-- Footer -->
            <div style="background-color: #f8fafc; padding: 25px; text-align: center; font-size: 14px; color: #64748b; border-radius: 0 0 8px 8px; border-left: 1px solid #e5e7eb; border-right: 1px solid #e5e7eb; border-bottom: 1px solid #e5e7eb;">
                <p style="margin-bottom: 10px;">&copy; 2025 Deal Sourcer. All rights reserved.</p>
                <p style="margin-top: 0;">Berlin, Germany</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(user.email, subject, html_content, text_content)

async def send_login_code_email(pool: asyncpg.Pool, email: str, access_code: str) -> bool:
    """
    Send login email with access code
    
    Args:
        pool: Database connection pool
        email: User email address
        access_code: Generated access code
        
    Returns:
        True if email sent successfully, False otherwise
    """
    async with pool.acquire() as conn:
        # Get user info from the database
        user_record = await conn.fetchrow(
            "SELECT first_name, last_name, company FROM users WHERE email = $1",
            email
        )
        
        if not user_record:
            return False
    
    subject = "Your Deal Sourcer Login Code"
    
    text_content = f"""
    Hello {user_record['first_name']},
    
    Here is your login code for Deal Sourcer:
    
    {access_code}
    
    This code will expire in 1 hour.
    
    Best regards,
    The Deal Sourcer Team
    Berlin, Germany
    """
    
    # Deal Sourcer brand colors
    brand_color = "#3b3992"  # Primary indigo blue
    brand_color_light = "#ecedf7"  # Very light shade for backgrounds
    brand_color_medium = "#9d9ccc"  # Medium shade for accents
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; color: #333333; line-height: 1.6; background-color: #f5f7fa;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <!-- Header with Logo -->
            <div style="background-color: {brand_color}; padding: 30px; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700;">Deal Sourcer</h1>
            </div>
            
            <!-- Main Content -->
            <div style="background-color: #ffffff; padding: 40px 30px; border-left: 1px solid #e5e7eb; border-right: 1px solid #e5e7eb; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);">
                <h2 style="color: {brand_color}; margin-top: 0; font-size: 22px;">Login Request</h2>
                <p style="margin-bottom: 25px;">Hello {user_record['first_name']},</p>
                <p>You've requested to log in to your Deal Sourcer account. Please use the verification code below to complete your login:</p>
                
                <!-- Code Box -->
                <div style="background-color: {brand_color_light}; border: 2px solid {brand_color}; border-radius: 8px; padding: 20px; margin: 30px 0; text-align: center;">
                    <p style="font-family: 'Courier New', monospace; font-size: 32px; font-weight: bold; letter-spacing: 6px; margin: 0; color: {brand_color};">{access_code}</p>
                </div>
                
                <p>This code will expire in 1 hour.</p>
                <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">If you did not request this login, please contact our support team immediately.</p>
            </div>
            
            <!-- Footer -->
            <div style="background-color: #f8fafc; padding: 25px; text-align: center; font-size: 14px; color: #64748b; border-radius: 0 0 8px 8px; border-left: 1px solid #e5e7eb; border-right: 1px solid #e5e7eb; border-bottom: 1px solid #e5e7eb;">
                <p style="margin-bottom: 10px;">&copy; 2025 Deal Sourcer. All rights reserved.</p>
                <p style="margin-top: 0;">Berlin, Germany</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return await send_email(email, subject, html_content, text_content)

async def verify_access_code(pool: asyncpg.Pool, email: str, code: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Verify an access code
    
    Args:
        pool: Database connection pool
        email: User email address
        code: Access code to verify
        
    Returns:
        Tuple of (is_valid, user_info)
        - is_valid: True if the code is valid and not expired
        - user_info: User information if the code is valid, None otherwise
    """
    try:
        async with pool.acquire() as conn:
            # Use prepared statement for fetching the access code
            # Note: asyncpg already uses prepared statements internally for parameterized queries
            access_code_record = await conn.fetchrow(
                """
                SELECT code, user_info, expires_at 
                FROM access_codes 
                WHERE email = $1 
                ORDER BY created_at DESC 
                LIMIT 1
                """,
                email
            )
            
            if not access_code_record:
                return False, None
            
            # Check if code has expired
            # Use timezone-aware datetime for comparison
            now = datetime.now(access_code_record['expires_at'].tzinfo)
            if now > access_code_record['expires_at']:
                # Delete expired code using prepared statement
                await conn.execute(
                    "DELETE FROM access_codes WHERE email = $1 AND code = $2",
                    email, access_code_record['code']
                )
                return False, None
            
            # Check if code matches (constant-time comparison for security)
            if not secrets.compare_digest(code, access_code_record['code']):
                return False, None
            
            # Code is valid, get user info
            user_info = json.loads(access_code_record['user_info'])
            
            # Clean up the verified code using prepared statement
            await conn.execute(
                "DELETE FROM access_codes WHERE email = $1 AND code = $2",
                email, code
            )
            
            # If this was a signup verification, create the user in the database
            # First check if user exists
            existing_user = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE email = $1",
                email
            )
            
            if existing_user == 0:
                # Create the user using prepared statement
                await conn.execute(
                    """
                    INSERT INTO users(email, first_name, last_name, company)
                    VALUES($1, $2, $3, $4)
                    """,
                    user_info['email'],
                    user_info['first_name'],
                    user_info['last_name'],
                    user_info.get('company', None)  # Explicitly handle None
                )
            
            return True, user_info
    except Exception as e:
        # Log the exception for debugging
        import logging
        logging.error(f"Error in verify_access_code: {str(e)}")
        # Re-raise for handling in the calling function
        raise

async def generate_token_for_user(user_info: Dict[str, Any]) -> TokenResponse:
    """
    Generate a JWT token for a verified user
    
    Args:
        user_info: User information from verification
        
    Returns:
        Token response with access token and user info
    """
    # Create token data from user info
    token_data = {
        "email": user_info["email"],
        "first_name": user_info["first_name"],
        "last_name": user_info["last_name"],
    }
    
    if "company" in user_info:
        token_data["company"] = user_info["company"]
    
    # Create the access token
    access_token = create_access_token(token_data)
    
    # Create user response object
    user = UserResponse(
        email=user_info["email"],
        first_name=user_info["first_name"],
        last_name=user_info["last_name"],
        company=user_info.get("company")
    )
    
    # Return token response
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )
