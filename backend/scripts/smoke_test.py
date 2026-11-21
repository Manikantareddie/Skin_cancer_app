"""Complete end-to-end smoke test for the FastAPI backend service."""
import base64
import io
import json
import socket
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from threading import Thread

# Ensure project root is in sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import uvicorn
from backend.app.main import app


def get_free_port():
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def run_smoke_test():
    port = get_free_port()
    base_url = f"http://127.0.0.1:{port}"
    print(f"Starting ephemeral test server on {base_url}...")

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)

    thread = Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server to boot
    for _ in range(30):
        time.sleep(0.5)
        try:
            with urllib.request.urlopen(f"{base_url}/api/v1/health", timeout=2) as resp:
                if resp.status == 200:
                    break
        except Exception:
            pass

    print("\n[SMOKE TEST 1: Health Check]")
    with urllib.request.urlopen(f"{base_url}/api/v1/health") as resp:
        assert resp.status == 200
        health_data = json.loads(resp.read().decode())
        print(f"PASS: {health_data}")

    print("\n[SMOKE TEST 2: Model Status]")
    with urllib.request.urlopen(f"{base_url}/api/v1/model/status") as resp:
        assert resp.status == 200
        model_data = json.loads(resp.read().decode())
        print(f"PASS: {model_data}")

    print("\n[SMOKE TEST 3: Image Analysis (Validation + ResNet Inference + Grad-CAM)]")
    sample_file = project_root / "data" / "samples" / "sample_lesion.png"
    assert sample_file.exists(), f"Sample image {sample_file} not found!"

    # Multi-part form-data boundary
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
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
        analysis_data = json.loads(resp.read().decode())
        print(f"Case ID: {analysis_data['case_id']}")
        print(f"Validation: is_valid={analysis_data['validation']['is_valid']}")
        print(f"Prediction: {analysis_data['prediction']}")
        print(f"Clinical Risk: {analysis_data['clinical_risk']}")
        print(f"Heatmap data URL length: {len(analysis_data['heatmap_base64'])}")
        print("PASS: Multimodal inference executed successfully!")

    print("\n[SMOKE TEST 4: AI Summary Fallback (NVIDIA Unconfigured)]")
    ai_payload = json.dumps({
        "case_id": analysis_data["case_id"],
        "predicted_label": analysis_data["prediction"]["predicted_label"],
        "confidence_score": analysis_data["prediction"]["confidence_score"],
        "risk_level": analysis_data["clinical_risk"]["risk_level"],
        "abcd_results": analysis_data["abcde"]["raw_dictionary"],
    }).encode()

    ai_req = urllib.request.Request(
        f"{base_url}/api/v1/ai/summary",
        data=ai_payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(ai_req) as resp:
        assert resp.status == 200
        ai_data = json.loads(resp.read().decode())
        print(f"Provider: {ai_data['provider']}")
        print(f"Summary excerpt: {ai_data['clinical_summary'][:120]}...")
        print("PASS: Safe deterministic fallback generated correctly!")

    print("\n[SMOKE TEST 5: PDF Report Streaming]")
    rep_boundary = "----WebKitFormBoundaryReportTest"
    rep_body = (
        f"--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="original_file"; filename="sample_lesion.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + img_bytes + (
        f"\r\n--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="heatmap_base64"\r\n\r\n'
        f"{analysis_data['heatmap_base64']}\r\n"
        f"--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="prediction"\r\n\r\n'
        f"{analysis_data['prediction']['predicted_label']}\r\n"
        f"--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="confidence"\r\n\r\n'
        f"{analysis_data['prediction']['confidence_score']}\r\n"
        f"--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="risk_level"\r\n\r\n'
        f"{analysis_data['clinical_risk']['risk_level']}\r\n"
        f"--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="abcd_results_json"\r\n\r\n'
        f"{json.dumps(analysis_data['abcde']['raw_dictionary'])}\r\n"
        f"--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="ai_summary"\r\n\r\n'
        f"Smoke Test Summary\r\n"
        f"--{rep_boundary}\r\n"
        f'Content-Disposition: form-data; name="case_id"\r\n\r\n'
        f"{analysis_data['case_id']}\r\n"
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
        assert pdf_bytes.startswith(b"%PDF-"), "Should return valid PDF header!"
        print(f"Received PDF stream: {len(pdf_bytes)} bytes starting with {pdf_bytes[:8]}")
        print("PASS: In-memory PDF streamed successfully!")

    print("\n" + "=" * 60)
    print("ALL 5 LIVE SMOKE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    server.should_exit = True


if __name__ == "__main__":
    run_smoke_test()
