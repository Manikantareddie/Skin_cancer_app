import streamlit as st
import requests


INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"


def _get_headers():
    if "NVIDIA_API_KEY" not in st.secrets:
        return None

    return {
        "Authorization": f"Bearer {st.secrets['NVIDIA_API_KEY']}",
        "Content-Type": "application/json"
    }


def _call_nvidia_model(prompt: str) -> str:
    headers = _get_headers()

    if headers is None:
        return "NVIDIA API key not configured."

    payload = {
        "model": "mistralai/ministral-14b-instruct-2512",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1024,
        "temperature": 0.3,
        "top_p": 1.0,
        "stream": False
    }

    try:
        response = requests.post(INVOKE_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    except Exception as e:
        return f"NVIDIA API Error: {str(e)}"


# ==========================================================
# PUBLIC FUNCTIONS (DO NOT CHANGE SIGNATURE)
# ==========================================================

def generate_ai_summary(payload: str) -> str:
    prompt = f"""
You are a medical AI assistant.

Given the following AI-based skin lesion analysis,
provide:
1. A concise clinical-style summary
2. Risk interpretation
3. Recommended next steps
4. Clear disclaimer

Rules:
- Do NOT diagnose
- Do NOT claim certainty
- Keep language professional and educational

DATA:
{payload}
"""
    return _call_nvidia_model(prompt)


def generate_patient_guidance(predicted_label, risk_level, abcd_results):
    prompt = f"""
You are a medical AI assistant helping patients understand
their skin lesion analysis report.

Prediction: {predicted_label}
Overall Risk Level: {risk_level}

ABCDE Findings:
{abcd_results}

Generate a calm, educational response.
Do NOT diagnose.
Do NOT prescribe medication.
"""
    return _call_nvidia_model(prompt)
