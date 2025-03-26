from fastapi import APIRouter, HTTPException, Depends

from app.models.auth import UserSignUp, VerifyCode, UserResponse, LoginRequest, LoginResponse, RequestLoginCode
from app.services.auth_service import (
    create_access_code, send_verification_email, verify_access_code, 
    generate_token_for_user, generate_login_code, send_login_code_email
)
from app.core.security import get_current_user
from app.core.config import settings
from app.core.dbconn import get_pool
from asyncpg.pool import Pool

router = APIRouter()

@router.post("/signup")
async def signup(user: UserSignUp, pool: Pool = Depends(get_pool)):
    """
    Handle user signup and send verification code via email
    """
    try:
        # Generate an access code
        access_code = await create_access_code(pool, user)
        
        # Send verification email
        email_sent = await send_verification_email(user, access_code)
        
        if not email_sent:
            raise HTTPException(status_code=500, detail="Failed to send verification email")
        
        return {"message": "Verification code sent to your email"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during signup: {str(e)}")

@router.post("/request-login-code")
async def request_login_code(request: RequestLoginCode, pool: Pool = Depends(get_pool)):
    """
    Request a login code for an existing user
    
    This will send an email with the code if the user exists.
    """
    try:
        # Generate login code
        success, result = await generate_login_code(pool, request.email)
        
        if not success:
            raise HTTPException(status_code=404, detail=result)  # result contains error message
        
        # If successful, result contains the access code
        # Send login code email
        email_sent = await send_login_code_email(pool, request.email, result)
        
        if not email_sent:
            raise HTTPException(status_code=500, detail="Failed to send login code email")
        
        return {"message": "Login code sent to your email"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error requesting login code: {str(e)}")

@router.post("/verify-code")
async def verify_code(verification: VerifyCode, pool: Pool = Depends(get_pool)):
    """
    Verify the access code provided by the user
    """
    try:
        # Verify the code
        is_valid, user_info = await verify_access_code(pool, verification.email, verification.access_code)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid or expired verification code")
        
        # Return the verified user information
        return {
            "message": "Verification successful",
            "user": UserResponse(
                email=user_info["email"],
                first_name=user_info["first_name"],
                last_name=user_info["last_name"],
                company=user_info.get("company")
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during verification: {str(e)}")

@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest, pool: Pool = Depends(get_pool)):
    """
    Login with email and access code, returning a JWT token
    """
    try:
        # Verify the code
        is_valid, user_info = await verify_access_code(pool, login_data.email, login_data.access_code)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail="Invalid or expired verification code")
        
        # Generate token for the user
        token = await generate_token_for_user(user_info)
        
        # Return login response
        return LoginResponse(
            message="Login successful",
            token=token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """
    Get current authenticated user information
    """
    return UserResponse(**current_user)

# Development-only endpoint to get a test token
# This should be disabled in production
@router.get("/test-token")
async def get_test_token(pool: Pool = Depends(get_pool)):
    """
    Get a test token for development purposes.
    
    **This endpoint should be disabled in production.**
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="Test token endpoint is only available in debug mode"
        )
    
    # Create dummy user info for the test token
    user_info = {
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "company": "Test Company"
    }
    
    # Check if test user exists, if not create it
    try:
        async with pool.acquire() as conn:
            exists = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE email = $1", 
                user_info["email"]
            )
            
            if exists == 0:
                # Create the test user
                await conn.execute(
                    """
                    INSERT INTO users(email, first_name, last_name, company)
                    VALUES($1, $2, $3, $4)
                    """,
                    user_info["email"],
                    user_info["first_name"],
                    user_info["last_name"],
                    user_info["company"]
                )
    except Exception:
        # If we can't create the user, just continue (it may already exist)
        pass
    
    # Generate token
    token = await generate_token_for_user(user_info)
    
    return {
        "note": "This token is for testing purposes only",
        "token": token.access_token,
        "token_with_bearer": f"Bearer {token.access_token}"
    }

@router.get("/dev-token")
async def get_dev_token(pool: Pool = Depends(get_pool)):
    """
    Get a token for the pre-created dev user for testing purposes.
    
    **This endpoint should be disabled in production.**
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="Dev token endpoint is only available in debug mode"
        )
    
    # Create user info for the dev token using our pre-created dev user
    user_info = {
        "email": "dev@example.com",
        "first_name": "Dev",
        "last_name": "User",
        "company": "TestCompany"
    }
    
    # Make sure our dev user exists
    try:
        async with pool.acquire() as conn:
            exists = await conn.fetchval(
                "SELECT COUNT(*) FROM users WHERE email = $1", 
                user_info["email"]
            )
            
            if exists == 0:
                # Create the dev user if it doesn't exist
                await conn.execute(
                    """
                    INSERT INTO users(email, first_name, last_name, company)
                    VALUES($1, $2, $3, $4)
                    """,
                    user_info["email"],
                    user_info["first_name"],
                    user_info["last_name"],
                    user_info["company"]
                )
    except Exception as e:
        # If we can't create the user, just continue (it may already exist)
        pass
    
    # Generate token
    token = await generate_token_for_user(user_info)
    
    return {
        "note": "This token is for development testing purposes only",
        "token": token.access_token,
        "token_with_bearer": f"Bearer {token.access_token}",
        "curl_example": f'curl -X GET "http://0.0.0.0:8000/search?participant_name=Rubens" -H "Authorization: Bearer {token.access_token}"'
    }
