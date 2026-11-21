from datetime import datetime
from fastapi import APIRouter, Response, status
from backend.app.core.config import settings
from backend.app.services.model_service import model_service

router = APIRouter()


@router.get("/health", tags=["System"])
def health_check():
    """Liveness probe: verifies the API service is alive and accepting traffic."""
    return {
        "status": "ok",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@router.get("/ready", tags=["System"])
def readiness_check(response: Response):
    """
    Readiness probe: distinguishes API server liveness from model inference readiness.
    Returns HTTP 200 when PyTorch model checkpoint is loaded.
    Returns HTTP 503 Service Unavailable when model is downloading, warming up, or encountered an error.
    """
    status_data = model_service.get_status()
    if status_data.is_loaded:
        return {
            "status": "ready",
            "model_loaded": True,
            "device": status_data.device,
            "architecture": status_data.architecture,
            "model_path": status_data.model_path,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    if model_service.load_error:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "error",
            "model_loaded": False,
            "error": model_service.load_error,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {
        "status": "loading",
        "model_loaded": False,
        "detail": "Model checkpoint is downloading or initializing in the background.",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
