from fastapi import APIRouter, HTTPException

from app.models.auth import UserSignUp, VerifyCode, UserResponse
from app.services.auth_service import create_access_code, send_verification_email, verify_access_code

router = APIRouter()

@router.post("/signup")
async def signup(user: UserSignUp):
    """
    Handle user signup and send verification code via email
    """
    try:
        # Generate an access code
        access_code = await create_access_code(user)
        
        # Send verification email
        email_sent = await send_verification_email(user, access_code)
        
        if not email_sent:
            raise HTTPException(status_code=500, detail="Failed to send verification email")
        
        return {"message": "Verification code sent to your email"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during signup: {str(e)}")

@router.post("/verify-code")
async def verify_code(verification: VerifyCode):
    """
    Verify the access code provided by the user
    """
    try:
        # Verify the code
        is_valid, user_info = await verify_access_code(verification.email, verification.access_code)
        
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
