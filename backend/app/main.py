from contextlib import asynccontextmanager
import logging
import re
import threading
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from backend.app.api.v1.router import api_router
from backend.app.core.config import settings
from backend.app.services.model_service import model_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("skin_cancer_backend")


def verify_opencv_runtime():
    """Validates that OpenCV is loaded and capable of Haar Cascade classification."""
    try:
        import cv2
        logger.info(f"OpenCV loaded from {getattr(cv2, '__file__', 'unknown')} (v{getattr(cv2, '__version__', 'unknown')})")
        assert hasattr(cv2, "CascadeClassifier"), "cv2 is missing CascadeClassifier"
        assert hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades"), "cv2.data.haarcascades is missing"
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        cascade = cv2.CascadeClassifier(cascade_path)
        assert not cascade.empty(), f"Haar cascade at {cascade_path} is empty"
        logger.info("OpenCV Haar cascade runtime check: PASSED")
        return True, "OpenCV Haar cascade operational"
    except Exception as exc:
        logger.error(f"OpenCV Haar cascade runtime check: FAILED: {exc}")
        return False, str(exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Background pre-warm for the PyTorch ResNet model checkpoint and runtime verification.
    Allows Uvicorn to bind to $PORT immediately on cold starts, passing Render health checks.
    """
    logger.info("Initializing runtime verifications and background model preload...")
    verify_opencv_runtime()

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
    allow_methods=["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches all unexpected exceptions and returns a consistent HTTP 500 JSON response
    with appropriate CORS headers attached so browsers never receive broken preflights
    or CORS errors on server failures.
    """
    logger.exception(f"Unhandled server error on {request.method} {request.url.path}: {exc}")
    origin = request.headers.get("origin")
    headers = {}
    allowed_origins = settings.get_allowed_origins()
    if origin:
        origin_clean = origin.strip().rstrip("/")
        if origin_clean in allowed_origins or re.match(settings.ALLOWED_ORIGIN_REGEX, origin_clean):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
            headers["Access-Control-Allow-Methods"] = "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"
            headers["Access-Control-Allow-Headers"] = "*"

    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
        headers=headers,
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
