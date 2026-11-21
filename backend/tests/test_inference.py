import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_analyze_endpoint():
    sample_path = Path("data/samples/sample_lesion.png")
    assert sample_path.exists()

    with open(sample_path, "rb") as f:
        response = client.post(
            "/api/v1/analyze",
            files={"file": ("sample_lesion.png", f, "image/png")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["case_id"].startswith("SKIN-")
    assert data["validation"]["is_valid"] is True
    assert data["prediction"]["predicted_label"] in ["Benign", "Malignant"]
    assert data["prediction"]["confidence_score"] > 0
    assert data["heatmap_base64"].startswith("data:image/png;base64,")
    assert data["clinical_risk"]["risk_level"] in ["LOW", "MODERATE", "HIGH"]


def test_ai_summary_fallback_endpoint():
    payload = {
        "case_id": "TEST-123",
        "predicted_label": "Benign",
        "confidence_score": 92.5,
        "risk_level": "LOW",
        "abcd_results": {
            "A – Asymmetry": "Low (0.12)",
            "B – Border": "Regular (1.20)",
            "C – Color": "Moderate (3 colors)",
            "D – Diameter": "4.50 mm (Below Risk Threshold)",
            "E – Evolution": "Stable",
        },
    }
    response = client.post("/api/v1/ai/summary", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "clinical_summary" in data
    assert "patient_guidance" in data
    assert "disclaimer" in data
    assert data["provider"] in ["deterministic_rules_engine", "gemini", "nvidia"]


def test_pdf_report_generation_endpoint():
    sample_path = Path("data/samples/sample_lesion.png")
    # First get analysis to get heatmap
    with open(sample_path, "rb") as f:
        res = client.post(
            "/api/v1/analyze",
            files={"file": ("sample_lesion.png", f, "image/png")},
        )
    analysis = res.json()

    with open(sample_path, "rb") as orig_f:
        rep_res = client.post(
            "/api/v1/report/generate",
            files={"original_file": ("sample_lesion.png", orig_f, "image/png")},
            data={
                "heatmap_base64": analysis["heatmap_base64"],
                "prediction": analysis["prediction"]["predicted_label"],
                "confidence": str(analysis["prediction"]["confidence_score"]),
                "risk_level": analysis["clinical_risk"]["risk_level"],
                "abcd_results_json": json.dumps(analysis["abcde"]["raw_dictionary"]),
                "ai_summary": "Test AI Summary for Report",
                "case_id": analysis["case_id"],
            },
        )

    assert rep_res.status_code == 200
    assert rep_res.headers["content-type"] == "application/pdf"
    assert rep_res.content.startswith(b"%PDF-")
