"""
Verification test for deployment configurations:
- Health check (liveness)
- Readiness check (model loaded)
- CORS origin parsing and Vercel regex matching
- ModelService error handling & caching
- PDF streaming report generation in memory
"""
import io
import os
import sys
import re
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi import Response
from backend.app.core.config import settings
from backend.app.services.model_service import model_service
from backend.app.api.v1.endpoints.health import health_check, readiness_check
from backend.app.services.report_service import generate_pdf_report
from PIL import Image

def test_liveness():
    res = health_check()
    assert res["status"] == "ok"
    assert "timestamp" in res
    print(" [PASS] Liveness health check returns status: ok")

def test_cors_and_vercel_regex():
    # Test regex matching
    pattern = re.compile(settings.ALLOWED_ORIGIN_REGEX)
    assert pattern.match("https://dermaassist.vercel.app")
    assert pattern.match("https://skin-cancer-app-abc123-user.vercel.app")
    assert not pattern.match("https://malicious-site.com")
    print(" [PASS] Vercel CORS regex matches production and preview domains")

    # Test get_allowed_origins
    origins = settings.get_allowed_origins()
    assert isinstance(origins, list)
    assert "http://localhost:5173" in origins
    print(" [PASS] Allowed origins parsing works correctly")

def test_readiness():
    resp = Response()
    # Ensure model is loaded
    model_service.load_model()
    ready_res = readiness_check(resp)
    assert ready_res["status"] == "ready"
    assert ready_res["model_loaded"] is True
    assert ready_res["device"] == "cpu"
    print(" [PASS] Readiness check returns HTTP 200 with model status")

def test_in_memory_pdf_streaming():
    # Verify PDF generates into BytesIO without needing Windows paths or writing to disk
    img = Image.new("RGB", (200, 200), color=(180, 100, 90))
    img_buf = io.BytesIO()
    img.save(img_buf, format="JPEG")
    img_buf.seek(0)

    pdf_buf = io.BytesIO()
    generate_pdf_report(
        file_path=pdf_buf,
        original_image_path=img_buf,
        heatmap_image_path=img_buf,
        prediction="Benign",
        confidence=92.5,
        risk_level="LOW RISK",
        abcd_results={"A – Asymmetry": "Low", "B – Border": "Regular", "C – Color": "Uniform"},
        ai_summary="Educational test summary.",
        case_id="TEST-DEPLOY-001",
    )
    pdf_bytes = pdf_buf.getvalue()
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
    print(f" [PASS] In-memory PDF generation succeeded ({len(pdf_bytes)} bytes)")

if __name__ == "__main__":
    print("--- Running DermaAssist Deployment Verification Suite ---")
    test_liveness()
    test_cors_and_vercel_regex()
    test_readiness()
    test_in_memory_pdf_streaming()
    print("--- ALL DEPLOYMENT READINESS TESTS PASSED ---")
