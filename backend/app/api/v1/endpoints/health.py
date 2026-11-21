from datetime import datetime
from fastapi import APIRouter
from backend.app.core.config import settings

router = APIRouter()


@router.get("/health", tags=["System"])
def health_check():
    """Health check endpoint for container uptime monitoring and cold-start detection."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
