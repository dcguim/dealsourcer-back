from fastapi import APIRouter
from app.api.endpoints import search, organizations, stats, auth

# Create the main API router
api_router = APIRouter()

# Include protected endpoint routers
api_router.include_router(search.router, tags=["search"])
api_router.include_router(organizations.router, tags=["organizations"])
api_router.include_router(stats.router, tags=["stats"])

# Include auth endpoints with a prefix and tags
api_router.include_router(
    auth.router,
    prefix="/api",
    tags=["auth"]
)

# Root endpoint
@api_router.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "api": "Organization Search API",
        "version": "1.0",
        "endpoints": [
            {"path": "/", "method": "GET", "description": "API information"},
            {"path": "/search", "method": "GET", "description": "Search organizations (requires auth)"},
            {"path": "/organization/{id}", "method": "GET", "description": "Get organization details (requires auth)"},
            {"path": "/stats", "method": "GET", "description": "Get database statistics (requires auth)"},
            {"path": "/api/signup", "method": "POST", "description": "Sign up for an account"},
            {"path": "/api/request-login-code", "method": "POST", "description": "Request a login code for existing users"},
            {"path": "/api/verify-code", "method": "POST", "description": "Verify email access code"},
            {"path": "/api/login", "method": "POST", "description": "Login and get JWT token"},
            {"path": "/api/me", "method": "GET", "description": "Get current user info (requires auth)"},
            {"path": "/api/test-token", "method": "GET", "description": "Get a test token (development only)"}
        ]
    }
