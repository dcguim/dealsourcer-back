import time
import traceback
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.dbconn import create_connection_pool, close_connection_pool
from app.api.routes import api_router
from app.core.logging import logger

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

# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    logger.error(f"HTTP error: {exc.detail}")
    return {"detail": exc.detail}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Validation error: {exc}")
    return {"detail": str(exc)}

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    error_detail = f"Unexpected error: {str(exc)}\n{traceback.format_exc()}"
    logger.error(error_detail)
    return {"detail": str(exc)}

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
