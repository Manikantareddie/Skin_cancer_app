import enum
import json
import re
from typing import Dict, List, Optional, Tuple
import httpx

from backend.app.core.config import settings
from backend.app.schemas.analysis import (
    AIExplanationResponse,
    ObservedFeature,
    StructuredAIExplanation,
)


from backend.app.schemas.measurements import (
    DiameterAssessment,
    DiameterProvenance,
    EvolutionAssessment,
    EvolutionProvenance,
)


class AIErrorType(str, enum.Enum):
    MISSING_CREDENTIALS = "MISSING_CREDENTIALS"
    INVALID_API_KEY = "INVALID_API_KEY"
    PERMISSION_FAILURE = "PERMISSION_FAILURE"
    UNSUPPORTED_MODEL = "UNSUPPORTED_MODEL"
    RATE_LIMIT = "RATE_LIMIT"
    TIMEOUT = "TIMEOUT"
    SERVER_ERROR = "SERVER_ERROR"
    UNKNOWN = "UNKNOWN"


def _build_structured_prompt(
    predicted_label: str,
    confidence_score: float,
    risk_level: str,
    abcd_results: Dict[str, str],
    diameter_assessment: Optional[DiameterAssessment] = None,
    evolution_assessment: Optional[EvolutionAssessment] = None,
) -> str:
    """
    Builds a normalized, privacy-preserving prompt containing verified clinical descriptors.
    No raw images or patient-identifying history (PII) are transmitted.
    """
    # Build Diameter Context
    d_context: Dict[str, object] = {}
    if diameter_assessment and diameter_assessment.status == DiameterProvenance.MEASURED:
        d_context = {
            "status": "MEASURED",
            "diameter_mm": diameter_assessment.longest_diameter_mm,
            "method": diameter_assessment.measurement_method,
            "clinical_guideline_context": "Classical ABCDE criteria reference 6mm as a guideline threshold; however, diameter alone is not diagnostic as small melanomas and large benign nevi both occur.",
        }
    elif diameter_assessment and diameter_assessment.status == DiameterProvenance.USER_REPORTED:
        d_context = {
            "status": "USER_REPORTED",
            "diameter_mm": diameter_assessment.longest_diameter_mm,
            "method": "Patient or clinician manual caliper entry",
            "clinical_guideline_context": "Self-reported measurement. Heuristic guideline threshold is 6mm.",
        }
    else:
        d_context = {
            "status": "UNAVAILABLE",
            "reason": "No in-frame calibrated millimeter scale or manual measurement provided.",
        }

    # Build Evolution Context
    e_context: Dict[str, object] = {}
    if evolution_assessment and evolution_assessment.status == EvolutionProvenance.OBSERVED:
        e_context = {
            "status": "OBSERVED",
            "time_interval": evolution_assessment.time_interval_display or "Multiple timepoints",
            "relative_area_change_percent": evolution_assessment.area_change_percent,
            "comparability_grade": evolution_assessment.comparability.value,
            "technical_confounders": evolution_assessment.technical_confounders.confounding_disclosures,
            "note": "Morphological delta observed via digital image registration. Pixel variations may stem from lighting or angle and do not confirm biological change without biopsy.",
        }
    elif evolution_assessment and evolution_assessment.status == EvolutionProvenance.REPORTED:
        reported_syms = []
        p_c = evolution_assessment.patient_reported_changes
        if p_c.size_change: reported_syms.append("size growth")
        if p_c.color_change: reported_syms.append("color darkening")
        if p_c.shape_change: reported_syms.append("shape irregularity")
        if p_c.itching: reported_syms.append("itching")
        if p_c.pain: reported_syms.append("pain")
        if p_c.bleeding: reported_syms.append("bleeding")
        e_context = {
            "status": "REPORTED",
            "patient_reported_changes": reported_syms or ["General change reported"],
            "note": "Documented purely from patient history; no comparable baseline image available.",
        }
    elif evolution_assessment and evolution_assessment.status == EvolutionProvenance.UNCERTAIN:
        e_context = {
            "status": "UNCERTAIN",
            "reason": "Sequential photos present, but technical disparities (camera angle, lighting, focus) prevent reliable delta computation.",
            "technical_confounders": evolution_assessment.technical_confounders.confounding_disclosures,
        }
    else:
        e_context = {
            "status": "NOT_ASSESSABLE",
            "reason": "Single static photograph snapshot; historical evolution requires sequential records.",
        }

    structured_findings = {
        "classifier_output": {
            "predicted_category": predicted_label,
            "raw_softmax_score_percentage": round(confidence_score, 2),
            "score_type": "Uncalibrated neural network softmax output score",
            "model_architecture": "Dual-branch ResNet18 + GLCM/Wavelet texture fusion",
            "benchmark_context": "Evaluated at 84.23% test accuracy and 80.89% recall on dermatological image sets",
        },
        "observed_image_features": {
            "A – Asymmetry": abcd_results.get("A – Asymmetry", "Assessed"),
            "B – Border": abcd_results.get("B – Border", "Assessed"),
            "C – Color": abcd_results.get("C – Color", "Assessed"),
        },
        "diameter_assessment": d_context,
        "evolution_assessment": e_context,
        "overall_screening_risk_level": risk_level,
    }

    findings_json = json.dumps(structured_findings, indent=2)

    return f"""You are an educational interpretation assistant for a dermatological clinical decision support research tool.

Given the following verified, structured image analysis findings:
{findings_json}

Your task is to generate an objective, responsible, educational explanation for the screening report.

STRICT CONSTRAINTS:
1. Output MUST be ONLY valid JSON adhering to the schema below. No conversational preambles, no greetings (e.g., do NOT write "Hello", "Thank you for sharing", "Don't worry").
2. Do NOT diagnose cancer or claim certainty. Use phrasing like "The model classified the image into the {predicted_label.lower()} category".
3. Strictly respect measurement provenance:
   - If Diameter is MEASURED or USER_REPORTED, discuss it with reference to the 6mm heuristic guideline (noting 6mm is not an absolute cutoff).
   - If Diameter is UNAVAILABLE, state clearly that physical scale was not calibrated.
   - If Evolution is OBSERVED, discuss the measured area change while noting that photographic differences can cause pixel variations.
   - If Evolution is REPORTED, highlight the patient-reported symptoms.
   - If Evolution is UNCERTAIN or NOT_ASSESSABLE, explain that longitudinal change could not be confirmed.
4. Never invent missing measurements or contradict the model's prediction.
5. Do NOT prescribe medications or clinical treatments.
6. Provide concise, readable, plain English without markdown tables.

REQUIRED JSON OUTPUT SCHEMA:
{{
  "result_explanation": "A concise 2-3 sentence explanation of what the model classified and what that classification means.",
  "observed_features": [
    {{
      "feature": "Asymmetry & Border",
      "explanation": "Concise interpretation of asymmetry and border regularity findings."
    }},
    {{
      "feature": "Color Distribution",
      "explanation": "Concise interpretation of color clustering findings."
    }},
    {{
      "feature": "Diameter Assessment",
      "explanation": "Concise interpretation reflecting measured, user-reported, or unavailable diameter status."
    }},
    {{
      "feature": "Evolution & History",
      "explanation": "Concise interpretation reflecting observed, reported, uncertain, or unassessable evolution status."
    }}
  ],
  "limitations": [
    "Machine learning classifiers can produce false positives and false negatives.",
    "This AI screening aid does not replace in-person dermatoscopic examination or histological biopsy."
  ],
  "next_steps": [
    "Consult a board-certified dermatologist for a comprehensive skin examination.",
    "Monitor the lesion for any changes in size, shape, color, or symptoms such as bleeding or itching."
  ]
}}
"""


def get_deterministic_explanation(
    predicted_label: str,
    confidence_score: float,
    risk_level: str,
    abcd_results: Dict[str, str],
    diameter_assessment: Optional[DiameterAssessment] = None,
    evolution_assessment: Optional[EvolutionAssessment] = None,
) -> AIExplanationResponse:
    """
    Deterministic rule-based clinical explanation fallback.
    Conforms to the exact same StructuredAIExplanation schema.
    Used when external APIs are unconfigured, unreachable, or fail validation.
    """
    is_malignant = predicted_label.lower() == "malignant"

    if is_malignant:
        result_explanation = (
            f"The research classifier placed this image in the '{predicted_label}' category with an output score of {confidence_score:.2f}%. "
            "This indicates that the lesion exhibits visual features similar to malignant training examples. "
            "This finding is an automated screening alert and does not constitute a confirmed diagnosis."
        )
    else:
        result_explanation = (
            f"The research classifier placed this image in the '{predicted_label}' category with an output score of {confidence_score:.2f}%. "
            "This indicates that the lesion demonstrates morphological features commonly associated with benign training samples. "
            "However, an automated screening result cannot definitively rule out abnormal pathology."
        )

    observed_features = []
    asym_val = abcd_results.get("A – Asymmetry", "Assessed")
    border_val = abcd_results.get("B – Border", "Assessed")
    observed_features.append(ObservedFeature(
        feature="Asymmetry & Border Regularity",
        explanation=f"Visual contour asymmetry was calculated as: {asym_val}; border irregularity index was calculated as: {border_val}.",
    ))

    color_val = abcd_results.get("C – Color", "Assessed")
    observed_features.append(ObservedFeature(
        feature="Color Variation",
        explanation=f"Dominant color cluster analysis identified: {color_val}.",
    ))

    # Diameter Explanation
    if diameter_assessment and diameter_assessment.status == DiameterProvenance.MEASURED:
        d_text = f"Longest diameter measured as {diameter_assessment.longest_diameter_mm:.1f} mm via calibrated ruler."
        if diameter_assessment.is_exceeding_6mm_guideline:
            d_text += " Note that 6 mm is a clinical guideline threshold, not a definitive diagnostic boundary."
    elif diameter_assessment and diameter_assessment.status == DiameterProvenance.USER_REPORTED:
        d_text = f"Patient/clinician reported diameter of {diameter_assessment.longest_diameter_mm:.1f} mm."
    else:
        d_text = "Physical diameter in millimeters cannot be determined without an in-frame calibrated reference scale."
    observed_features.append(ObservedFeature(
        feature="Diameter Assessment",
        explanation=d_text,
    ))

    # Evolution Explanation
    if evolution_assessment and evolution_assessment.status == EvolutionProvenance.OBSERVED:
        delta_str = f"{'+' if evolution_assessment.area_change_percent and evolution_assessment.area_change_percent > 0 else ''}{evolution_assessment.area_change_percent}%"
        e_text = f"Sequential image registration observed an apparent 2D area change of {delta_str} ({evolution_assessment.comparability.value} comparability)."
    elif evolution_assessment and evolution_assessment.status == EvolutionProvenance.REPORTED:
        e_text = "Patient-reported historical evolution noted in lesion size, shape, color, or symptoms."
    elif evolution_assessment and evolution_assessment.status == EvolutionProvenance.UNCERTAIN:
        e_text = "Sequential photos submitted, but camera angle or lighting variations prevent objective biological confirmation."
    else:
        e_text = "Single static photograph snapshot; chronological evolution requires longitudinal sequential photos."
    observed_features.append(ObservedFeature(
        feature="Evolution & History",
        explanation=e_text,
    ))

    limitations = [
        "Clinical guideline: 6 mm is a heuristic reference, not an absolute boundary (small melanomas and large benign nevi both occur).",
        "Photographic differences (lighting, camera distance, angle) can simulate physical variation and do not confirm biological progression.",
        "Model benchmark performance is 84.23% accuracy and 80.89% recall; false positives and false negatives occur.",
    ]

    next_steps = [
        "Schedule an in-person clinical evaluation with a board-certified dermatologist for professional dermoscopy.",
        "Perform regular skin self-examinations and seek prompt medical attention if you notice changes in size, shape, or color.",
    ]

    structured = StructuredAIExplanation(
        result_explanation=result_explanation,
        observed_features=observed_features,
        limitations=limitations,
        next_steps=next_steps,
    )

    disclaimer = (
        "Educational Screening Limitation Notice: This assessment is generated by an experimental clinical decision support model. "
        "It does not provide a definitive medical diagnosis and cannot replace in-person consultation with a physician."
    )

    # Pre-render text for backward compatibility / PDF export
    summary_text = (
        f"AI Screening Result: {result_explanation}\n\n"
        "Observed Characteristics:\n" +
        "\n".join(f"• {f.feature}: {f.explanation}" for f in observed_features)
    )
    guidance_text = (
        "Next Steps:\n" + "\n".join(f"• {s}" for s in next_steps) +
        "\n\nLimitations:\n" + "\n".join(f"• {l}" for l in limitations)
    )

    return AIExplanationResponse(
        provider="deterministic_rules_engine",
        is_fallback=True,
        explanation=structured,
        disclaimer=disclaimer,
        clinical_summary=summary_text,
        patient_guidance=guidance_text,
    )


def _extract_json_block(text: str) -> Optional[str]:
    """
    Safely extracts a valid JSON block from raw LLM output.
    Handles reasoning traces, thought tags, code fences, and preambles.
    """
    if not text:
        return None

    # Strip thinking tags if present (<think>...</think>)
    if "<think>" in text and "</think>" in text:
        text = text.split("</think>", 1)[1]

    # 1. Search for all code fences ```json ... ``` or ``` ... ```
    fence_matches = list(re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE))
    if fence_matches:
        # Check fences in reverse order (reasoning models usually put the final JSON in the last fence)
        for match in reversed(fence_matches):
            candidate = match.group(1).strip()
            start_idx = candidate.find("{")
            end_idx = candidate.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                sub = candidate[start_idx : end_idx + 1]
                try:
                    parsed = json.loads(sub)
                    if isinstance(parsed, dict) and "result_explanation" in parsed:
                        return sub
                except Exception:
                    pass

    # 2. If no valid fence, search for balanced outermost { ... }
    # Scan backward from the last '}' to find matching '{'
    r_idx = text.rfind("}")
    if r_idx != -1:
        l_indices = [i for i, ch in enumerate(text[:r_idx]) if ch == "{"]
        for l_idx in reversed(l_indices):
            candidate = text[l_idx : r_idx + 1]
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict) and "result_explanation" in parsed:
                    return candidate
            except Exception:
                continue

    # 3. Fallback: widest first { to last }
    start_idx = text.find("{")
    end_idx = text.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        candidate = text[start_idx : end_idx + 1]
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass

    return None


def call_nvidia_api(
    prompt: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
) -> Tuple[Optional[str], Optional[AIErrorType], Optional[str]]:
    """Calls NVIDIA NIM / OpenAI-compatible Chat Completions API with robust error classification."""
    effective_key = settings.NVIDIA_API_KEY if api_key is None else api_key
    effective_model = settings.NVIDIA_MODEL if model is None else model
    effective_base_url = (settings.NVIDIA_BASE_URL if base_url is None else base_url).rstrip("/")

    if not effective_key:
        return None, AIErrorType.MISSING_CREDENTIALS, "NVIDIA API key is not configured."

    url = f"{effective_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {effective_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": effective_model,
        "messages": [
            {
                "role": "system",
                "content": "You are a clinical AI explanation service. Return ONLY valid JSON conforming to the requested schema. Do NOT include markdown code blocks, preambles, or conversational greetings."
            },
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2048,
        "temperature": 0.2,
        "stream": False,
    }

    try:
        with httpx.Client(timeout=45.0) as client:
            resp = client.post(url, headers=headers, json=payload)

        if resp.status_code == 200:
            data = resp.json()
            message = data["choices"][0]["message"]
            content = message.get("content") or message.get("reasoning_content")
            return content, None, None

        status = resp.status_code
        error_text = resp.text[:250]

        if status == 401:
            return None, AIErrorType.INVALID_API_KEY, f"Invalid NVIDIA API key (HTTP 401): {error_text}"
        elif status == 403:
            return None, AIErrorType.PERMISSION_FAILURE, f"Permission denied for model '{effective_model}' (HTTP 403): {error_text}"
        elif status in [404, 410] or (status == 400 and ("model" in error_text.lower() or "not found" in error_text.lower())):
            return None, AIErrorType.UNSUPPORTED_MODEL, f"Model '{effective_model}' not found or no longer available (HTTP {status}): {error_text}"
        elif status == 429:
            return None, AIErrorType.RATE_LIMIT, f"Rate limit reached on NVIDIA API (HTTP 429): {error_text}"
        elif status >= 500:
            return None, AIErrorType.SERVER_ERROR, f"NVIDIA server error (HTTP {status}): {error_text}"
        else:
            return None, AIErrorType.UNKNOWN, f"NVIDIA API Error (HTTP {status}): {error_text}"

    except httpx.TimeoutException:
        return None, AIErrorType.TIMEOUT, "NVIDIA API request timed out after 45 seconds."
    except Exception as e:
        return None, AIErrorType.UNKNOWN, f"Network error calling NVIDIA API: {str(e)}"


def generate_explanation(
    predicted_label: str,
    confidence_score: float,
    risk_level: str,
    abcd_results: Dict[str, str],
    diameter_assessment: Optional[DiameterAssessment] = None,
    evolution_assessment: Optional[EvolutionAssessment] = None,
) -> AIExplanationResponse:
    """
    Orchestrates structured AI clinical explanation via NVIDIA NIM API.
    Parses and validates the response into StructuredAIExplanation.
    Gracefully falls back to a deterministic explanation on any network, timeout, or schema failure.
    """
    disclaimer = (
        "Educational Screening Limitation Notice: This assessment is generated by an experimental clinical decision support model. "
        "It does not provide a definitive medical diagnosis and cannot replace in-person consultation with a physician."
    )

    if settings.NVIDIA_API_KEY:
        prompt = _build_structured_prompt(
            predicted_label,
            confidence_score,
            risk_level,
            abcd_results,
            diameter_assessment=diameter_assessment,
            evolution_assessment=evolution_assessment,
        )
        raw_text, err_type, err_msg = call_nvidia_api(prompt)

        if raw_text:
            json_str = _extract_json_block(raw_text)
            if json_str:
                try:
                    parsed_dict = json.loads(json_str)
                    structured_explanation = StructuredAIExplanation.model_validate(parsed_dict)

                    # Build summary texts for report compatibility
                    summary_text = (
                        f"AI Screening Result: {structured_explanation.result_explanation}\n\n"
                        "Observed Characteristics:\n" +
                        "\n".join(f"• {f.feature}: {f.explanation}" for f in structured_explanation.observed_features)
                    )
                    guidance_text = (
                        "Next Steps:\n" + "\n".join(f"• {s}" for s in structured_explanation.next_steps) +
                        "\n\nLimitations:\n" + "\n".join(f"• {l}" for l in structured_explanation.limitations)
                    )

                    return AIExplanationResponse(
                        provider="nvidia",
                        is_fallback=False,
                        explanation=structured_explanation,
                        disclaimer=disclaimer,
                        clinical_summary=summary_text,
                        patient_guidance=guidance_text,
                    )
                except Exception as parse_err:
                    fallback = get_deterministic_explanation(
                        predicted_label,
                        confidence_score,
                        risk_level,
                        abcd_results,
                        diameter_assessment=diameter_assessment,
                        evolution_assessment=evolution_assessment,
                    )
                    fallback.error = f"NVIDIA output failed JSON schema validation ({str(parse_err)}); falling back to deterministic explanation."
                    return fallback

        # If call failed or returned empty
        fallback = get_deterministic_explanation(
            predicted_label,
            confidence_score,
            risk_level,
            abcd_results,
            diameter_assessment=diameter_assessment,
            evolution_assessment=evolution_assessment,
        )
        fallback.error = f"NVIDIA API Error ({err_type}): {err_msg}"
        return fallback

    # If no key configured
    fallback = get_deterministic_explanation(
        predicted_label,
        confidence_score,
        risk_level,
        abcd_results,
        diameter_assessment=diameter_assessment,
        evolution_assessment=evolution_assessment,
    )
    fallback.error = "NVIDIA API key not configured; using deterministic clinical rules engine."
    return fallback
