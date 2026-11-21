"""Isolated test script for NVIDIA NIM API integration."""
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.core.config import settings
from backend.app.services.ai_service import call_nvidia_api, AIErrorType


def test_nvidia():
    print("=" * 60)
    print("NVIDIA NIM API INTEGRATION TEST")
    print("=" * 60)
    print(f"Target Base URL: {settings.NVIDIA_BASE_URL}")
    print(f"Configured Model: {settings.NVIDIA_MODEL}")
    key_configured = bool(settings.NVIDIA_API_KEY)
    print(f"API Key Configured: {'YES (masked)' if key_configured else 'NO (empty)'}")

    test_prompt = "Hello. Respond in one brief sentence confirming you are functional."

    print("\n[TEST 1: Missing Credentials Check]")
    content, err_type, err_msg = call_nvidia_api(test_prompt, api_key="")
    print(f"Expected: MISSING_CREDENTIALS")
    print(f"Result Error Type: {err_type}")
    print(f"Result Message: {err_msg}")
    assert err_type == AIErrorType.MISSING_CREDENTIALS, "Should detect missing credentials!"
    print("PASS: Missing credentials correctly classified.")

    print("\n[TEST 2: Invalid API Key Classification Check]")
    content, err_type, err_msg = call_nvidia_api(test_prompt, api_key="nvapi-invalid-test-key-12345")
    print(f"Result Error Type: {err_type}")
    print(f"Result Message: {err_msg}")
    # Under live network, status is 401 (INVALID_API_KEY). If network is unreachable, it's UNKNOWN.
    assert err_type in [AIErrorType.INVALID_API_KEY, AIErrorType.PERMISSION_FAILURE, AIErrorType.UNKNOWN], f"Unexpected error type: {err_type}"
    print("PASS: Invalid API key attempt correctly handled and classified.")

    if key_configured:
        print("\n[TEST 3: Live Configured NVIDIA Request Check]")
        content, err_type, err_msg = call_nvidia_api(test_prompt)
        if content:
            print(f"SUCCESS! NVIDIA Model Response:\n{content}")
        else:
            print(f"FAILED. Error Type: {err_type}")
            print(f"Error Details: {err_msg}")

    print("=" * 60)


if __name__ == "__main__":
    test_nvidia()
