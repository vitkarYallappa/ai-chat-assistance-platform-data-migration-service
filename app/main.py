"""
Main application module for the Data Migration Service.

This module creates and configures the FastAPI application.
"""
import asyncio
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

from app.api.routes import api_router
from app.config import Settings, get_settings
from app.core.exceptions import setup_exception_handlers
from app.core.logging import configure_logging, request_middleware
from app.utils.database import init_database


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        settings: Optional settings instance
        
    Returns:
        Configured FastAPI application
    """
    if settings is None:
        settings = get_settings()
    
    # Configure logging
    configure_logging(log_level=settings.LOG_LEVEL, json_logs=settings.JSON_LOGS)
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.APP_NAME,
        description="Service for coordinating database migrations across sharded databases",
        version="0.1.0",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        docs_url=f"{settings.API_PREFIX}/docs",
        redoc_url=f"{settings.API_PREFIX}/redoc",
        debug=settings.DEBUG,
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add request middleware for logging and context
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        return await request_middleware(request, call_next)
    
    # Set up global exception handlers
    setup_exception_handlers(app)
    
    # Mount metrics endpoint
    metrics_app = make_asgi_app()
    app.mount(f"{settings.API_PREFIX}/metrics", metrics_app)
    
    # Include API router
    app.include_router(api_router, prefix=settings.API_PREFIX)
    
    # Add startup and shutdown events
    @app.on_event("startup")
    async def startup_event():
        """Initialize the application on startup."""
        # Initialize database
        await init_database()
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Clean up resources on shutdown."""
        # Clean up any resources here
        pass
    
    # Add health check endpoint
    @app.get(f"{settings.API_PREFIX}/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return JSONResponse(
            content={"status": "ok", "service": settings.APP_NAME}, 
            status_code=200
        )
    
    return app


# For running the application directly
app = create_app()


if __name__ == "__main__":
    """Run the application using Uvicorn when executed directly."""
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8005,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )