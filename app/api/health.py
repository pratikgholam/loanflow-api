"""Health check route."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """Return API health status."""
    return {"status": "healthy"}
