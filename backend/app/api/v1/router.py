from fastapi import APIRouter
from backend.app.api.v1.endpoints import (
    ai_explanation,
    analyze,
    evolution,
    health,
    measurements,
    model,
    report,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["System"])
api_router.include_router(model.router, prefix="/model", tags=["Model"])
api_router.include_router(analyze.router, tags=["Inference"])
api_router.include_router(measurements.router, prefix="/measurements", tags=["Measurements"])
api_router.include_router(evolution.router, prefix="/evolution", tags=["Evolution"])
api_router.include_router(ai_explanation.router, prefix="/ai", tags=["AI Explanation"])
api_router.include_router(report.router, prefix="/report", tags=["Report"])
