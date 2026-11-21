from contextlib import asynccontextmanager
import logging
import threading
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from backend.app.api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.services.model_service import model_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("skin_cancer_backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Background pre-warm for the PyTorch ResNet model checkpoint.
    Allows the Uvicorn HTTP server to bind to $PORT immediately on cold starts,
    passing Render/cloud liveness health checks without timeout.
    """
    logger.info("Initializing background model preload...")
    warmup_thread = threading.Thread(
        target=lambda: _safe_preload(),
        daemon=True,
        name="model-preloader",
    )
    warmup_thread.start()
    yield
    logger.info("Application shutting down.")


def _safe_preload():
    try:
        model_service.load_model()
        logger.info("PyTorch model successfully loaded in background.")
    except Exception as exc:
        logger.warning(f"Background model warmup failed (will retry on first request): {exc}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="REST API for clinical skin lesion decision support, Grad-CAM explainability, and AI summaries.",
    lifespan=lifespan,
)

# CORS configuration supporting exact origins and Vercel dynamic preview domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_origin_regex=settings.ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root-level health & readiness endpoints for Render / container healthchecks
@app.get("/health", tags=["System"], include_in_schema=False)
def root_health():
    from backend.app.api.v1.endpoints.health import health_check
    return health_check()


@app.get("/ready", tags=["System"], include_in_schema=False)
def root_ready(response: Response):
    from backend.app.api.v1.endpoints.health import readiness_check
    return readiness_check(response)


app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/docs")
