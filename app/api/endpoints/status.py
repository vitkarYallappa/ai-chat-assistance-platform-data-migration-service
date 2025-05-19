"""
Placeholder module for status endpoints.

This module will be fully implemented in Phase 2.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_status():
    """Placeholder endpoint to get migration status."""
    return {"message": "Status endpoint - to be implemented"}