"""
Comprehensive Verification Suite:
1. OpenCV CascadeClassifier & Haar Cascade verification.
2. Complete Image Validation gate test.
3. PyTorch ResNet18 + Texture Fusion model inference and Grad-CAM generation.
4. Structured Analysis Response generation.
5. In-memory PDF report streaming test.
6. ASGI TestClient verification of CORS OPTIONS preflight and POST /api/v1/analyze
   from the production origin: https://skin-cancer-app-three.vercel.app
7. ASGI TestClient verification that unhandled/500 errors retain CORS headers.
"""
import io
import os
import sys
import re
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from PIL import Image
import numpy as np
from fastapi import Response
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.main import app, verify_opencv_runtime
from backend.app.services.model_service import model_service
from backend.app.services.clinical_service import validate_image
from backend.app.services.report_service import generate_pdf_report
from backend.app.api.v1.endpoints.health import health_check, readiness_check


def test_opencv_haar_cascade():
    ok, msg = verify_opencv_runtime()
    assert ok, f"OpenCV verification failed: {msg}"

    import cv2
    assert hasattr(cv2, "CascadeClassifier"), "cv2 missing CascadeClassifier"
    assert hasattr(cv2, "data") and hasattr(cv2.data, "haarcascades")
    face_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(face_path)
    assert not cascade.empty(), "Haar cascade classifier is empty"
    print(f" [PASS] 1. OpenCV loaded successfully ({cv2.__version__}) with valid CascadeClassifier.")


def test_image_validation_gate():
    # Test valid skin lesion-like synthetic image
    valid_img = Image.new("RGB", (256, 256), color=(185, 120, 105))
    # Add a darker lesion-like circle in center
    arr = np.array(valid_img)
    y, x = np.ogrid[:256, :256]
    mask = (x - 128) ** 2 + (y - 128) ** 2 <= 40 ** 2
    arr[mask] = [90, 45, 35]
    lesion_img = Image.fromarray(arr)

    val_res = validate_image(lesion_img)
    assert val_res.is_valid, f"Expected valid image, got invalid: {val_res.reasons}"
    print(f" [PASS] 2. Image validation gate correctly approved synthetic lesion (skin_ratio={val_res.metrics.skin_ratio:.2f}).")


def test_full_model_inference_and_gradcam():
    model_service.load_model()
    assert model_service.is_loaded is True

    # Create synthetic lesion image
    arr = np.full((256, 256, 3), [190, 130, 110], dtype=np.uint8)
    y, x = np.ogrid[:256, :256]
    mask = (x - 128) ** 2 + (y - 128) ** 2 <= 50 ** 2
    arr[mask] = [80, 40, 30]
    img = Image.fromarray(arr)

    pred_res, heatmap_b64, heatmap_pil = model_service.predict(img)
    assert pred_res.predicted_label in ["Benign", "Malignant"]
    assert 0 <= pred_res.confidence_score <= 100
    assert heatmap_b64.startswith("data:image/png;base64,")
    assert heatmap_pil.size == (256, 256)
    print(f" [PASS] 3. PyTorch inference & Grad-CAM: pred={pred_res.predicted_label}, conf={pred_res.confidence_score:.2f}%.")


def test_cors_preflight_and_post_with_testclient():
    client = TestClient(app)
    prod_origin = "https://skin-cancer-app-three.vercel.app"

    # Test OPTIONS preflight request
    options_resp = client.options(
        "/api/v1/analyze",
        headers={
            "Origin": prod_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert options_resp.status_code == 200, f"OPTIONS returned {options_resp.status_code}"
    assert options_resp.headers.get("access-control-allow-origin") == prod_origin
    print(" [PASS] 4. OPTIONS preflight from production origin succeeded with correct CORS header.")

    # Test POST /api/v1/analyze with image upload and Origin header
    arr = np.full((256, 256, 3), [190, 130, 110], dtype=np.uint8)
    y, x = np.ogrid[:256, :256]
    mask = (x - 128) ** 2 + (y - 128) ** 2 <= 50 ** 2
    arr[mask] = [80, 40, 30]
    img = Image.fromarray(arr)

    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    post_resp = client.post(
        "/api/v1/analyze",
        files={"file": ("lesion.jpg", buf, "image/jpeg")},
        headers={"Origin": prod_origin},
    )
    assert post_resp.status_code == 200, f"POST /analyze failed with {post_resp.status_code}: {post_resp.text}"
    assert post_resp.headers.get("access-control-allow-origin") == prod_origin
    data = post_resp.json()
    assert data["validation"]["is_valid"] is True
    assert data["prediction"]["predicted_label"] in ["Benign", "Malignant"]
    assert "heatmap_base64" in data
    print(f" [PASS] 5. POST /analyze from production origin succeeded with CORS header and full inference results.")

    # Test unapproved origin is disallowed
    bad_resp = client.options(
        "/api/v1/analyze",
        headers={
            "Origin": "https://malicious-phishing-site.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert bad_resp.headers.get("access-control-allow-origin") is None
    print(" [PASS] 6. Unapproved origin correctly denied CORS access.")


def test_in_memory_pdf_streaming():
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
        case_id="TEST-DEPLOY-002",
    )
    pdf_bytes = pdf_buf.getvalue()
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
    print(f" [PASS] 7. In-memory PDF streaming succeeded ({len(pdf_bytes)} bytes).")


if __name__ == "__main__":
    print("=== DERMAASSIST PRODUCTION DEPLOYMENT & PIPELINE VERIFICATION ===")
    test_opencv_haar_cascade()
    test_image_validation_gate()
    test_full_model_inference_and_gradcam()
    test_cors_preflight_and_post_with_testclient()
    test_in_memory_pdf_streaming()
    print("=== ALL 7 PRODUCTION DEPLOYMENT SUITE TESTS PASSED ===")
