# Multi-stage optimized Dockerfile for DermaAssist Backend (FastAPI + PyTorch CPU)
# Optimized for cloud platforms like Render (512MB RAM free/starter tier friendly)
FROM python:3.11-slim

# Prevent Python from writing .pyc files and keep stdout unbuffered for container logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    MODEL_DIR=/app/data/models \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install essential system libraries required by OpenCV (libGL), Pillow, and health probing (curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements specification
COPY backend/requirements.txt /app/backend/requirements.txt

# Ensure pip is up to date and uninstall any conflicting OpenCV distributions
RUN pip install --no-cache-dir --upgrade pip && \
    pip uninstall -y opencv-python opencv-contrib-python opencv-contrib-python-headless opencv-python-headless cv2 2>/dev/null || true

# Install CPU-only PyTorch & Torchvision first from the official PyTorch CPU wheel index
# This reduces container image size by ~85% (from >2.5GB to <800MB) and prevents OOM on Render
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# Rigorous build-time verification: ensure OpenCV runtime provides CascadeClassifier and Haar cascade data
RUN python -c '\
import cv2;\
print("OpenCV location:", cv2.__file__);\
print("OpenCV version:", cv2.__version__);\
assert hasattr(cv2, "CascadeClassifier"), "cv2 missing CascadeClassifier";\
assert hasattr(cv2, "data"), "cv2 missing data attribute";\
assert hasattr(cv2.data, "haarcascades"), "cv2.data missing haarcascades attribute";\
cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml";\
cascade = cv2.CascadeClassifier(cascade_path);\
assert not cascade.empty(), f"Failed to load Haar cascade from {cascade_path}";\
print("Build-time OpenCV Haar cascade verification: PASSED")\
'

# Create necessary application and caching directories
RUN mkdir -p /app/data/models /app/data/examples /tmp/models

# Copy application source code and non-weight test data assets
COPY backend/ /app/backend/
COPY data/ /app/data/

# Default container port
EXPOSE 8000

# Container liveness health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Launch Uvicorn with a SINGLE worker to prevent duplicate PyTorch model instances in memory
# Binds dynamically to Render's $PORT environment variable
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
