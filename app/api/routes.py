from fastapi import APIRouter
from app.api.endpoints import search, organizations, stats, auth

# Create the main API router
api_router = APIRouter()

# Include all endpoint routers
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
            {"path": "/search", "method": "GET", "description": "Search organizations by name, description, or ID"},
            {"path": "/organization/{id}", "method": "GET", "description": "Get organization details by ID"},
            {"path": "/stats", "method": "GET", "description": "Get database statistics"},
            {"path": "/api/signup", "method": "POST", "description": "Sign up for an account"},
            {"path": "/api/verify-code", "method": "POST", "description": "Verify email access code"}
        ]
    }
