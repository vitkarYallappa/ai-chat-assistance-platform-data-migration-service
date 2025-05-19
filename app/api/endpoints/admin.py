"""
Placeholder module for admin endpoints.

This module will be fully implemented in Phase 2.
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def admin_dashboard():
    """Placeholder endpoint for admin dashboard."""
    return {"message": "Admin endpoint - to be implemented"}