import time
import traceback
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.config import settings
from app.core.dbconn import create_connection_pool, close_connection_pool
from app.api.routes import api_router
from app.core.logging import logger
from app.core.security import oauth2_scheme

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    debug=settings.DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)

# Custom OpenAPI to include security scheme
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description="Organization Search API with JWT authentication",
        routes=app.routes,
    )
    
    # Add security scheme component
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
        
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Don't set global security - let each endpoint handle it through dependencies
    if "security" in openapi_schema:
        del openapi_schema["security"]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Set custom OpenAPI schema
app.openapi = custom_openapi

# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP error: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    error_detail = f"Unexpected error: {str(exc)}\n{traceback.format_exc()}"
    logger.error(error_detail)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Create database connection pool on startup"""
    logger.info("Starting up application")
    try:
        await create_connection_pool()
        logger.info("Database connection pool created")
    except Exception as e:
        logger.error(f"Failed to create database connection pool: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection pool on shutdown"""
    logger.info("Shutting down application")
    await close_connection_pool()

# Performance monitoring middleware
@app.middleware("http")
async def log_and_add_process_time_header(request: Request, call_next):
    """Add processing time to response headers and log requests/responses"""
    start_time = time.time()
    
    logger.info(f"Request: {request.method} {request.url.path}?{request.url.query}")
    
    try:
        response = await call_next(request)
        
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        logger.info(f"Response: {response.status_code} - Took {process_time:.4f}s")
        
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        process_time = time.time() - start_time
        logger.error(f"Failed request took {process_time:.4f}s")
        raise

if __name__ == "__main__":
    import uvicorn
    
    # Run the application
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000,
        reload=settings.DEBUG,
        workers=4
    )
