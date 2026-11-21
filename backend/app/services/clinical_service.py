from typing import Dict, List, Optional
from PIL import Image

from backend.app.ml.diameter import calculate_diameter_assessment
from backend.app.ml.evolution import compare_evolution
from backend.app.ml.utils import (
    validate_skin_lesion_image,
    compute_asymmetry,
    compute_border_irregularity,
    compute_color_variation,
)
from backend.app.schemas.analysis import (
    ABCDEIndicators,
    ClinicalRiskResult,
    ImageValidationResult,
    ValidationMetrics,
)
from backend.app.schemas.measurements import (
    DiameterAssessment,
    DiameterProvenance,
    EvolutionAssessment,
    EvolutionProvenance,
)


def validate_image(pil_image: Image.Image) -> ImageValidationResult:
    """Validate lesion focus and skin context using existing multi-stage gate."""
    is_valid, reasons, metrics = validate_skin_lesion_image(pil_image)
    return ImageValidationResult(
        is_valid=is_valid,
        reasons=reasons,
        metrics=ValidationMetrics(
            width=metrics["width"],
            height=metrics["height"],
            contrast=float(metrics["contrast"]),
            skin_ratio=float(metrics["skin_ratio"]),
            largest_contour_ratio=float(metrics["largest_contour_ratio"]),
            abnormal_region_ratio=float(metrics["abnormal_region_ratio"]),
            face_detected=bool(metrics["face_detected"]),
            document_like=bool(metrics.get("document_like", False)),
        ),
    )


def extract_abcde_indicators(
    pil_image: Image.Image,
    diameter_assessment: Optional[DiameterAssessment] = None,
    evolution_assessment: Optional[EvolutionAssessment] = None,
) -> ABCDEIndicators:
    """
    Extract computer-vision ABCDE image features.
    
    Adheres strictly to medical validity:
    - Asymmetry, Border, Color: Computed from computer-vision morphology.
    - Diameter: Calibrated scale (MEASURED), patient input (USER_REPORTED), or UNAVAILABLE. Never arbitrary.
    - Evolution: Registered delta (OBSERVED), patient history (REPORTED), UNCERTAIN, or NOT_ASSESSABLE.
    """
    asymmetry_score = compute_asymmetry(pil_image)
    border_score = compute_border_irregularity(pil_image)
    color_count = compute_color_variation(pil_image)

    asym_label = (
        "Low" if asymmetry_score < 0.20 else
        "Moderate" if asymmetry_score < 0.50 else
        "High" if asymmetry_score < 0.75 else
        "Severe"
    )

    border_label = (
        "Regular" if border_score < 1.5 else
        "Mild Irregularity" if border_score < 2.0 else
        "Irregular" if border_score < 2.5 else
        "Highly Irregular"
    )

    color_label = (
        "Low" if color_count <= 2 else
        "Moderate" if color_count == 3 else
        "High"
    )

    # Use provided diameter assessment or generate unavailable baseline
    d_eval = diameter_assessment or calculate_diameter_assessment(pil_image)
    if d_eval.status == DiameterProvenance.MEASURED and d_eval.longest_diameter_mm is not None:
        diameter_display = f"Measured: {d_eval.longest_diameter_mm:.1f} mm (via calibrated ruler)"
    elif d_eval.status == DiameterProvenance.USER_REPORTED and d_eval.longest_diameter_mm is not None:
        diameter_display = f"Reported: {d_eval.longest_diameter_mm:.1f} mm (patient/clinician entry)"
    else:
        diameter_display = "Physical diameter cannot be determined from this image"

    # Use provided evolution assessment or generate single-image baseline
    e_eval = evolution_assessment or compare_evolution(pil_image)
    if e_eval.status == EvolutionProvenance.OBSERVED:
        delta_str = f"{'+' if e_eval.area_change_percent and e_eval.area_change_percent > 0 else ''}{e_eval.area_change_percent}%" if e_eval.area_change_percent is not None else "measured"
        evolution_display = f"Observed: {delta_str} relative area change ({e_eval.comparability.value} comparability)"
    elif e_eval.status == EvolutionProvenance.REPORTED:
        evolution_display = "Reported: Patient-documented changes in size, shape, color, or sensation"
    elif e_eval.status == EvolutionProvenance.UNCERTAIN:
        evolution_display = "Uncertain: Confounding photographic factors prevent biological confirmation"
    else:
        evolution_display = "Not assessable — requires previous images or clinical history"

    raw_dict = {
        "A – Asymmetry": f"{asym_label} (index: {asymmetry_score:.2f})",
        "B – Border": f"{border_label} (compactness: {border_score:.2f})",
        "C – Color": f"{color_label} ({color_count} dominant clusters)",
        "D – Diameter": diameter_display,
        "E – Evolution": evolution_display,
    }

    return ABCDEIndicators(
        asymmetry_score=asymmetry_score,
        asymmetry_label=asym_label,
        border_score=border_score,
        border_label=border_label,
        color_count=color_count,
        color_label=color_label,
        diameter_display=diameter_display,
        evolution_display=evolution_display,
        diameter=d_eval,
        evolution=e_eval,
        raw_dictionary=raw_dict,
    )


def evaluate_clinical_risk(
    abcde: ABCDEIndicators,
    predicted_label: str,
    confidence_score: float,
) -> ClinicalRiskResult:
    """
    Evaluates observed morphological and longitudinal risk factors.
    Provides clear, non-alarmist categorization and responsible next step recommendations.
    Does not treat 6mm as a definitive diagnostic threshold.
    """
    risk_score = 0
    reasons: List[str] = []

    if abcde.asymmetry_label in ["High", "Severe"]:
        risk_score += 1
        reasons.append("Elevated visual asymmetry observed in lesion shape")

    if abcde.border_label in ["Irregular", "Highly Irregular"]:
        risk_score += 1
        reasons.append("Irregular or poorly circumscribed lesion boundary detected")

    if abcde.color_label in ["Moderate", "High"]:
        risk_score += 1
        reasons.append("Multiple distinct color clusters identified across lesion")

    if predicted_label == "Malignant" and confidence_score >= 70:
        risk_score += 2
        reasons.append("Model classification placed image in malignant training category")

    # Longitudinal and Diameter contextual considerations
    if abcde.diameter:
        if abcde.diameter.is_exceeding_6mm_guideline:
            reasons.append(
                f"Lesion diameter ({abcde.diameter.longest_diameter_mm:.1f} mm, {abcde.diameter.status.value.lower()}) meets classical ABCDE >6 mm guideline; noting diameter alone is non-diagnostic"
            )

    if abcde.evolution:
        if abcde.evolution.status == EvolutionProvenance.OBSERVED and abcde.evolution.area_change_percent is not None:
            if abcde.evolution.area_change_percent > 15.0:
                risk_score += 1
                reasons.append(f"Longitudinal image comparison observed significant lesion expansion (+{abcde.evolution.area_change_percent}%)")
        elif abcde.evolution.status == EvolutionProvenance.REPORTED:
            p_changes = abcde.evolution.patient_reported_changes
            if p_changes.bleeding or p_changes.pain:
                risk_score += 1
                reasons.append("Patient-reported active symptoms (spontaneous bleeding or pain)")
            elif p_changes.size_change or p_changes.color_change:
                reasons.append("Patient-reported evolution in lesion size or coloration")

    if risk_score >= 3:
        risk_level, risk_class = "HIGH", "high"
        recommendation = "Prompt in-person clinical examination by a board-certified dermatologist is advised."
    elif risk_score >= 1:
        risk_level, risk_class = "MODERATE", "mid"
        recommendation = "Routine in-person dermatological evaluation recommended to confirm findings."
    else:
        risk_level, risk_class = "LOW", "low"
        recommendation = "Maintain regular skin self-examinations and seek medical review if changes occur."

    return ClinicalRiskResult(
        risk_level=risk_level,
        risk_class=risk_class,
        risk_score=risk_score,
        risk_reasons=reasons,
        clinical_recommendation=recommendation,
    )
