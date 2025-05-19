"""
API routes for the Data Migration Service.

This module configures the API router and includes all endpoint routers.
"""
from fastapi import APIRouter

# Import endpoint routers
# These will be implemented in Phase 2, but we set up the structure now
from app.api.endpoints import admin, migrations, status

# Create main API router
api_router = APIRouter()

# Include endpoint routers with prefixes
api_router.include_router(migrations.router, prefix="/migrations", tags=["Migrations"])
api_router.include_router(status.router, prefix="/status", tags=["Status"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])

# Create placeholder endpoints until the real ones are implemented
@api_router.get("/")
async def root():
    """Root endpoint for testing."""
    return {"message": "Data Migration Service API"}