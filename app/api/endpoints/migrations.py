
"""
Placeholder module for migration endpoints.

This module will be fully implemented in Phase 2.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def list_migrations():
    """Placeholder endpoint to list migrations."""
    return {"message": "Migrations endpoint - to be implemented"}