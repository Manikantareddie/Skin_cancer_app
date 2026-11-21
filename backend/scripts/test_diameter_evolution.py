"""
Comprehensive Verification Suite for Diameter (D) & Evolution (E) Assessment.
Tests:
1. Ruler calibration against images with known physical dimensions.
2. Manual user-reported measurements and guideline threshold logic.
3. Identical-image longitudinal comparison (0% delta baseline).
4. Images taken with different lighting, scale, and orientation (confounder detection).
5. Cases with missing history (NOT_ASSESSABLE and REPORTED).
6. Updated NVIDIA structured context and ReportLab PDF report generation.
"""
import io
import math
import sys
from datetime import datetime
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.ml.diameter import (
    calculate_diameter_assessment,
    calibrate_two_points,
    segment_lesion_contour,
)
from backend.app.ml.evolution import compare_evolution
from backend.app.schemas.measurements import (
    CalibrationPoint,
    ComparabilityGrade,
    DiameterProvenance,
    EvolutionProvenance,
    PatientReportedChanges,
)
from backend.app.services.ai_service import generate_explanation
from backend.app.services.clinical_service import (
    extract_abcde_indicators,
    evaluate_clinical_risk,
)
from backend.app.services.report_service import generate_pdf_report


def create_synthetic_ruler_image(
    width: int = 400,
    height: int = 400,
    lesion_radius_px: int = 50,  # 100px diameter
    pixels_per_mm: float = 10.0, # 10 px = 1 mm -> 100px = 10 mm
) -> Tuple[Image.Image, CalibrationPoint, CalibrationPoint, float]:
    """
    Creates a synthetic image with skin tone background, dark central lesion of known radius,
    and a millimeter ruler with tick marks at known coordinates.
    """
    # Skin background (warm tan RGB: 235, 205, 185)
    img = np.full((height, width, 3), (185, 205, 235), dtype=np.uint8)  # BGR

    # Central dark brown/black circular lesion
    cv2.circle(img, (width // 2, height // 2), lesion_radius_px, (30, 45, 80), -1)  # BGR dark brown

    # Draw a ruler at the bottom: y = 350
    # Tick 1 at x = 50, Tick 2 at x = 150 (distance = 100 px = 10.0 mm)
    p1 = CalibrationPoint(x=50.0, y=350.0)
    p2 = CalibrationPoint(x=150.0, y=350.0)
    physical_distance_mm = 10.0

    # Draw ruler base bar
    cv2.line(img, (30, 350), (370, 350), (255, 255, 255), 4)
    # Major ticks every 10 mm (100 px)
    for x in range(50, 360, 100):
        cv2.line(img, (x, 340), (x, 360), (255, 255, 255), 3)
    # Minor ticks every 1 mm (10 px)
    for x in range(50, 360, 10):
        cv2.line(img, (x, 345), (x, 355), (200, 200, 200), 1)

    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    return pil_img, p1, p2, physical_distance_mm


def test_suite():
    print("=" * 60)
    print("DERMAASSIST CRITERIA D & E COMPREHENSIVE VERIFICATION SUITE")
    print("=" * 60)

    # -------------------------------------------------------------
    # TEST 1: Ruler Calibration against known physical dimensions
    # -------------------------------------------------------------
    print("\n--- TEST 1: Ruler Calibration with Known Dimensions ---")
    known_pixels_per_mm = 10.0
    known_lesion_diameter_mm = 10.0  # 100px diameter at 10px/mm
    pil_test_img, p1, p2, phys_mm = create_synthetic_ruler_image(
        width=400, height=400, lesion_radius_px=50, pixels_per_mm=known_pixels_per_mm
    )

    # Calibrate
    calib = calibrate_two_points(p1, p2, phys_mm)
    print(f"1.1 Two-point distance in pixels: {calib.pixel_distance:.2f} px")
    print(f"1.2 Calculated scale: {calib.pixels_per_mm:.2f} px/mm (Expected: {known_pixels_per_mm})")
    assert abs(calib.pixels_per_mm - known_pixels_per_mm) < 0.1, "Calibrated scale must match synthetic scale"

    # Segment and measure diameter
    d_eval = calculate_diameter_assessment(pil_test_img, calibration_result=calib)
    print(f"1.3 Longest Feret diameter: {d_eval.longest_diameter_mm} mm (Expected ~10.0 mm)")
    print(f"1.4 Provenance: {d_eval.status}")
    print(f"1.5 Exceeds 6mm guideline: {d_eval.is_exceeding_6mm_guideline}")
    assert d_eval.status == DiameterProvenance.MEASURED
    assert d_eval.longest_diameter_mm is not None
    assert abs(d_eval.longest_diameter_mm - known_lesion_diameter_mm) <= 1.0, "Measured diameter should be ~10mm"
    assert d_eval.is_exceeding_6mm_guideline is True
    print(">>> TEST 1 PASSED: Precise physical scale and Feret diameter verified.")

    # -------------------------------------------------------------
    # TEST 2: Manual Measurements & Non-Definitive Guideline
    # -------------------------------------------------------------
    print("\n--- TEST 2: Manual Measurements & 6mm Heuristic Context ---")
    d_manual = calculate_diameter_assessment(pil_test_img, manual_diameter_mm=7.8)
    print(f"2.1 Manual diameter: {d_manual.longest_diameter_mm} mm")
    print(f"2.2 Provenance: {d_manual.status}")
    print(f"2.3 Exceeds 6mm guideline: {d_manual.is_exceeding_6mm_guideline}")
    assert d_manual.status == DiameterProvenance.USER_REPORTED
    assert d_manual.longest_diameter_mm == 7.8
    assert d_manual.is_exceeding_6mm_guideline is True
    assert "not a definitive diagnostic boundary" in d_manual.guideline_note

    d_unavail = calculate_diameter_assessment(pil_test_img)
    print(f"2.4 Unavailable status: {d_unavail.status}")
    assert d_unavail.status == DiameterProvenance.UNAVAILABLE
    assert d_unavail.longest_diameter_mm is None
    print(">>> TEST 2 PASSED: Manual input and unavailable fallbacks strictly preserved.")

    # -------------------------------------------------------------
    # TEST 3: Identical-Image Longitudinal Comparison (0% Delta)
    # -------------------------------------------------------------
    print("\n--- TEST 3: Identical-Image Comparison ---")
    sample_file = project_root / "data" / "samples" / "sample_lesion.png"
    sample_img = Image.open(sample_file).convert("RGB")

    e_identical = compare_evolution(
        followup_image=sample_img,
        baseline_image=sample_img,
        baseline_date="2025-01-15",
        followup_date="2025-07-15",
    )
    print(f"3.1 Comparability: {e_identical.comparability.value}")
    print(f"3.2 Provenance: {e_identical.status}")
    print(f"3.3 Area change percent: {e_identical.area_change_percent}% (Expected ~0.0%)")
    print(f"3.4 Color shift metric: {e_identical.color_shift_metric} (Expected 0.0)")
    print(f"3.5 Time interval display: {e_identical.time_interval_display}")
    assert e_identical.status == EvolutionProvenance.OBSERVED
    assert e_identical.comparability in [ComparabilityGrade.HIGH, ComparabilityGrade.MODERATE]
    assert e_identical.area_change_percent is not None and abs(e_identical.area_change_percent) < 1.0
    assert e_identical.difference_overlay_base64 is not None
    print(">>> TEST 3 PASSED: Identical images register with ~0% delta and difference overlay.")

    # -------------------------------------------------------------
    # TEST 4: Images with Different Lighting, Angle & Orientation
    # -------------------------------------------------------------
    print("\n--- TEST 4: Perturbed Lighting, Scale & Angle Confounders ---")
    # Perturb the sample image: brighten significantly (+60) and rotate 15 degrees
    sample_cv = np.array(sample_img)
    h, w = sample_cv.shape[:2]
    M_rot = cv2.getRotationMatrix2D((w / 2, h / 2), 15, 1.15)  # 15 deg rot, 1.15 zoom
    rotated_cv = cv2.warpAffine(sample_cv, M_rot, (w, h), borderMode=cv2.BORDER_REFLECT)
    brightened_cv = np.clip(rotated_cv.astype(np.int16) + 65, 0, 255).astype(np.uint8)
    perturbed_img = Image.fromarray(brightened_cv)

    e_perturbed = compare_evolution(
        followup_image=perturbed_img,
        baseline_image=sample_img,
        baseline_date="2024-06-01",
        followup_date="2025-06-01",
    )
    print(f"4.1 Comparability: {e_perturbed.comparability.value}")
    print(f"4.2 Status: {e_perturbed.status}")
    print(f"4.3 Confounders Detected: {len(e_perturbed.technical_confounders.confounding_disclosures)}")
    for conf in e_perturbed.technical_confounders.confounding_disclosures:
        print(f"    - {conf}")

    assert len(e_perturbed.technical_confounders.confounding_disclosures) > 0, "Must disclose photographic confounders"
    assert e_perturbed.status in [EvolutionProvenance.UNCERTAIN, EvolutionProvenance.OBSERVED]
    print(">>> TEST 4 PASSED: Technical confounders (lighting/angle/zoom) identified and disclosed.")

    # -------------------------------------------------------------
    # TEST 5: Missing History (NOT_ASSESSABLE vs REPORTED)
    # -------------------------------------------------------------
    print("\n--- TEST 5: Single Photograph & Patient Symptoms ---")
    # Single image with no reported symptoms
    e_none = compare_evolution(followup_image=sample_img)
    print(f"5.1 No history status: {e_none.status}")
    assert e_none.status == EvolutionProvenance.NOT_ASSESSABLE

    # Single image with patient-reported itching and bleeding
    p_changes = PatientReportedChanges(
        size_change=True,
        itching=True,
        bleeding=True,
        patient_notes="Noticed bleeding when washing lesion.",
    )
    e_reported = compare_evolution(
        followup_image=sample_img,
        reported_changes=p_changes,
    )
    print(f"5.2 Patient symptoms status: {e_reported.status}")
    print(f"5.3 Clinical summary: {e_reported.clinical_summary}")
    assert e_reported.status == EvolutionProvenance.REPORTED
    assert "bleeding" in e_reported.clinical_summary.lower()
    print(">>> TEST 5 PASSED: Provenance strictly tracks unassessable vs. patient-reported history.")

    # -------------------------------------------------------------
    # TEST 6: NVIDIA Structured Explanation & PDF Report Generation
    # -------------------------------------------------------------
    print("\n--- TEST 6: NVIDIA Explanation & PDF Report Integration ---")
    abcde = extract_abcde_indicators(
        sample_img,
        diameter_assessment=d_eval,
        evolution_assessment=e_identical,
    )
    risk = evaluate_clinical_risk(abcde, "Benign", 92.5)

    print(f"6.1 ABCDE D display: {abcde.diameter_display}")
    print(f"6.2 ABCDE E display: {abcde.evolution_display}")
    print(f"6.3 Clinical priority: {risk.risk_level}")

    ai_explanation = generate_explanation(
        predicted_label="Benign",
        confidence_score=92.5,
        risk_level=risk.risk_level,
        abcd_results=abcde.raw_dictionary,
        diameter_assessment=d_eval,
        evolution_assessment=e_identical,
    )
    print(f"6.4 AI Explanation Provider: {ai_explanation.provider} (Fallback: {ai_explanation.is_fallback})")
    print(f"6.5 AI Features Described: {len(ai_explanation.explanation.observed_features)}")
    for f in ai_explanation.explanation.observed_features:
        print(f"    • {f.feature}: {f.explanation[:65]}...")

    # PDF Report generation
    pdf_out = project_root / "data" / "samples" / "test_full_de_report.pdf"
    orig_buf = io.BytesIO()
    sample_img.save(orig_buf, format="PNG")
    orig_buf.seek(0)

    # Difference image buffer
    import base64
    diff_b64 = e_identical.difference_overlay_base64
    if "," in diff_b64: diff_b64 = diff_b64.split(",", 1)[1]
    diff_buf = io.BytesIO(base64.b64decode(diff_b64))

    generate_pdf_report(
        file_path=str(pdf_out),
        original_image_path=orig_buf,
        heatmap_image_path=orig_buf,
        prediction="Benign",
        confidence=92.5,
        risk_level=risk.risk_level,
        abcd_results=abcde.raw_dictionary,
        ai_summary=ai_explanation.clinical_summary,
        case_id="TEST-DE-2026",
        difference_image_path=diff_buf,
        diameter_detail=f"Measured {d_eval.longest_diameter_mm} mm via calibrated ruler",
        evolution_detail=e_identical.clinical_summary,
    )

    assert pdf_out.exists() and pdf_out.stat().st_size > 1000
    print(f"6.6 Generated PDF with difference overlay at {pdf_out.name} ({pdf_out.stat().st_size} bytes)")
    print(">>> TEST 6 PASSED: NVIDIA explanation and ReportLab PDF generated with rich D & E data.")

    print("\n" + "=" * 60)
    print("[ALL 6 TESTS PASSED WITH 100% SUCCESS]")
    print("=" * 60)


if __name__ == "__main__":
    test_suite()
