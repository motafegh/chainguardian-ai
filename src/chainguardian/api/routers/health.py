"""
Health check endpoints for monitoring and liveness probes.
"""
from fastapi import APIRouter

# Create router (like a mini-app for related endpoints)
router = APIRouter(
    tags=["health"]  # Groups endpoints in API docs
)


@router.get("/health")
async def health_check():
    """
    Health check endpoint for Kubernetes/Docker liveness probes.
    
    Returns:
        dict: Status information
    """
    return {
        "status": "healthy",
        "service": "chainguardian-ai",
        "version": "1.0.0"
    }


@router.get("/")
async def root():
    """
    Root endpoint with API information.
    
    Returns:
        dict: API metadata
    """
    return {
        "message": "ChainGuardian AI - ML-Powered Smart Contract Auditing",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
