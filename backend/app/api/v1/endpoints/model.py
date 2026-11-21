from fastapi import APIRouter
from backend.app.schemas.analysis import ModelStatusResponse
from backend.app.services.model_service import model_service

router = APIRouter()


@router.get("/status", response_model=ModelStatusResponse, tags=["Model"])
def get_model_status():
    """Returns the initialization, device, and checkpoint status of the deep learning model."""
    return model_service.get_status()


@router.post("/load", response_model=ModelStatusResponse, tags=["Model"])
def trigger_model_load():
    """Explicitly triggers downloading and loading the model checkpoint into memory."""
    model_service.load_model()
    return model_service.get_status()
