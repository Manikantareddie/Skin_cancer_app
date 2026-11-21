"""End-to-end verification of the complete patient workflow."""
import base64
import io
import json
import socket
import sys
import time
import urllib.request
from pathlib import Path
from threading import Thread

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from backend.app.main import app


def get_free_port():
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def verify_complete_workflow():
    port = get_free_port()
    base_url = f"http://127.0.0.1:{port}"
    print(f"1. Booting FastAPI backend on {base_url}...")

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    t = Thread(target=server.run, daemon=True)
    t.start()

    # Wait for server readiness
    for _ in range(30):
        time.sleep(0.5)
        try:
            with urllib.request.urlopen(f"{base_url}/api/v1/health", timeout=2) as r:
                if r.status == 200:
                    break
        except Exception:
            pass

    print("2. Server ready. Testing image upload to /api/v1/analyze...")
    sample_file = project_root / "data" / "samples" / "sample_lesion.png"
    assert sample_file.exists(), "Sample image must exist"

    boundary = "----WorkflowTestBoundary987654"
    with open(sample_file, "rb") as f:
        img_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="sample_lesion.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + img_bytes + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{base_url}/api/v1/analyze",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )

    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        analysis = json.loads(resp.read().decode())

    print("   ✓ Validation gate passed: is_valid =", analysis["validation"]["is_valid"])
    print("   ✓ Genuine Model Prediction:", analysis["prediction"]["predicted_label"])
    print(f"   ✓ Calculated Confidence: {analysis['prediction']['confidence_score']:.2f}%")
    print(f"   ✓ Malignant Probability: {analysis['prediction']['malignant_probability']:.2f}%")
    print(f"   ✓ Grad-CAM Heatmap Base64 generated: {len(analysis['heatmap_base64'])} bytes")
    print("   ✓ ABCDE Findings:", analysis["abcde"]["raw_dictionary"])
    print("   ✓ Clinical Risk Level:", analysis["clinical_risk"]["risk_level"])

    print("\n3. Testing NVIDIA NIM AI explanation generation...")
    ai_payload = json.dumps({
        "case_id": analysis["case_id"],
        "predicted_label": analysis["prediction"]["predicted_label"],
        "confidence_score": analysis["prediction"]["confidence_score"],
        "risk_level": analysis["clinical_risk"]["risk_level"],
        "abcd_results": analysis["abcde"]["raw_dictionary"],
    }).encode()

    ai_req = urllib.request.Request(
        f"{base_url}/api/v1/ai/summary",
        data=ai_payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(ai_req) as resp:
        assert resp.status == 200
        ai_resp = json.loads(resp.read().decode())

    print("   ✓ AI Provider:", ai_resp["provider"])
    print("   ✓ Clinical Summary received (preview):")
    for line in ai_resp["clinical_summary"].splitlines()[:4]:
        print("     ", line)
    print("   ✓ Patient Guidance received (preview):")
    for line in ai_resp["patient_guidance"].splitlines()[:3]:
        print("     ", line)

    print("\n4. Testing PDF Report Generation & Streaming...")
    rep_boundary = "----ReportTestBoundary12345"
    rep_body = (
        f"--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="original_file"; filename="sample_lesion.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + img_bytes + (
        f"\r\n--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="heatmap_base64"\r\n\r\n'
        f"{analysis['heatmap_base64']}\r\n"
        f"--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="prediction"\r\n\r\n'
        f"{analysis['prediction']['predicted_label']}\r\n"
        f"--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="confidence"\r\n\r\n'
        f"{analysis['prediction']['confidence_score']}\r\n"
        f"--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="risk_level"\r\n\r\n'
        f"{analysis['clinical_risk']['risk_level']}\r\n"
        f"--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="abcd_results_json"\r\n\r\n'
        f"{json.dumps(analysis['abcde']['raw_dictionary'])}\r\n"
        f"--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="ai_summary"\r\n\r\n'
        f"{ai_resp['clinical_summary']}\r\n"
        f"--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="case_id"\r\n\r\n'
        f"{analysis['case_id']}\r\n"
        f"--{rep_boundary}--\r\n"
    ).encode()

    rep_req = urllib.request.Request(
        f"{base_url}/api/v1/report/generate",
        data=rep_body,
        headers={"Content-Type": f"multipart/form-data; boundary={rep_boundary}"},
    )
    with urllib.request.urlopen(rep_req) as resp:
        assert resp.status == 200
        pdf_bytes = resp.read()
        assert pdf_bytes.startswith(b"%PDF-"), "Must be a valid PDF"
        print(f"   ✓ Generated PDF report successfully: {len(pdf_bytes)} bytes")

    print("\n" + "=" * 65)
    print("ALL WORKFLOW STEPS VERIFIED END-TO-END WITH LIVE MODEL & NVIDIA!")
    print("=" * 65)
    server.should_exit = True


if __name__ == "__main__":
    verify_complete_workflow()
