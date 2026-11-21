import base64
import io
import math
from datetime import datetime
from typing import List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image

from backend.app.ml.diameter import segment_lesion_contour
from backend.app.schemas.measurements import (
    ComparabilityGrade,
    EvolutionAssessment,
    EvolutionProvenance,
    PatientReportedChanges,
    TechnicalConfounders,
)


def compute_blur_metric(gray_img: np.ndarray) -> float:
    """Calculates variance of the Laplacian as a metric of visual sharpness."""
    return float(cv2.Laplacian(gray_img, cv2.CV_64F).var())


def compute_color_histogram_distance(img1_rgb: np.ndarray, img2_rgb: np.ndarray) -> float:
    """
    Computes Bhattacharyya distance between 3D RGB color histograms.
    0.0 = identical distribution; > 0.4 = significant color/lighting shift.
    """
    hist1 = cv2.calcHist([img1_rgb], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    hist2 = cv2.calcHist([img2_rgb], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
    cv2.normalize(hist1, hist1, alpha=1.0, norm_type=cv2.NORM_L1)
    cv2.normalize(hist2, hist2, alpha=1.0, norm_type=cv2.NORM_L1)
    return float(cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA))


def register_images(
    baseline_cv: np.ndarray,
    followup_cv: np.ndarray,
) -> Tuple[Optional[np.ndarray], bool, float, List[str]]:
    """
    Attempts feature-based image alignment using tuned ORB and Homography with RANSAC.
    Falls back to phase correlation if corner density is low (common in dermatoscopic images).
    Returns:
    - aligned_baseline_cv (or None)
    - alignment_success (bool)
    - inlier_ratio (float)
    - technical_warnings (List[str])
    """
    warnings: List[str] = []
    h_foll, w_foll = followup_cv.shape[:2]

    # Fast path: Check for identical or nearly identical image
    if baseline_cv.shape == followup_cv.shape:
        diff = float(np.mean(np.abs(baseline_cv.astype(np.float32) - followup_cv.astype(np.float32))))
        if diff < 1.5:
            return baseline_cv.copy(), True, 1.0, []

    gray_base = cv2.cvtColor(baseline_cv, cv2.COLOR_RGB2GRAY)
    gray_foll = cv2.cvtColor(followup_cv, cv2.COLOR_RGB2GRAY)

    # Detect features with tuned ORB (fastThreshold=5 to capture subtle dermatological features)
    orb = cv2.ORB_create(nfeatures=2500, fastThreshold=5, edgeThreshold=10)
    kp1, des1 = orb.detectAndCompute(gray_base, None)
    kp2, des2 = orb.detectAndCompute(gray_foll, None)

    if des1 is not None and des2 is not None and len(kp1) >= 4 and len(kp2) >= 4:
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        matches = sorted(matches, key=lambda x: x.distance)

        if len(matches) >= 4:
            src_pts = np.float32([kp1[m.queryIdx].pt for m in matches]).reshape(-1, 1, 2)
            dst_pts = np.float32([kp2[m.trainIdx].pt for m in matches]).reshape(-1, 1, 2)

            H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            if H is not None and mask is not None:
                inlier_ratio = float(np.sum(mask) / len(mask))
                det = float(np.linalg.det(H[:2, :2]))

                if 0.1 <= det <= 10.0:
                    if inlier_ratio < 0.25:
                        warnings.append("High geometric distortion detected (low inlier consensus ratio).")
                    aligned_baseline = cv2.warpPerspective(baseline_cv, H, (w_foll, h_foll))
                    return aligned_baseline, True, inlier_ratio, warnings

    # Fallback: Phase correlation alignment for translation matching
    if gray_base.shape == gray_foll.shape:
        try:
            shift, response = cv2.phaseCorrelate(np.float32(gray_base), np.float32(gray_foll))
            if response > 0.20:
                M_trans = np.float32([[1, 0, shift[0]], [0, 1, shift[1]]])
                aligned_baseline = cv2.warpAffine(baseline_cv, M_trans, (w_foll, h_foll))
                return aligned_baseline, True, float(response), ["Spatial correspondence established via cross-correlation."]
        except Exception:
            pass

    warnings.append("Insufficient distinctive visual features to register the two photographs.")
    return None, False, 0.0, warnings


def generate_difference_overlay(
    followup_rgb: np.ndarray,
    baseline_mask: np.ndarray,
    followup_mask: np.ndarray,
) -> str:
    """
    Creates an informative visual difference overlay showing:
    - Green: Stable shared lesion area
    - Amber/Red: Area newly covered in the follow-up image (apparent expansion)
    - Blue: Area covered only in the baseline image (apparent retraction/clearance)
    Returns a Base64 data URL.
    """
    overlay = followup_rgb.copy()
    h, w = followup_rgb.shape[:2]

    # Ensure masks match dimensions
    if baseline_mask.shape[:2] != (h, w):
        baseline_mask = cv2.resize(baseline_mask, (w, h), interpolation=cv2.INTER_NEAREST)
    if followup_mask.shape[:2] != (h, w):
        followup_mask = cv2.resize(followup_mask, (w, h), interpolation=cv2.INTER_NEAREST)

    base_bin = (baseline_mask > 0).astype(np.uint8)
    foll_bin = (followup_mask > 0).astype(np.uint8)

    shared = (base_bin & foll_bin) > 0
    expansion = (foll_bin > 0) & (~shared)
    regression = (base_bin > 0) & (~shared)

    # Tint regions:
    # Shared: Emerald Green (0, 200, 100)
    # Expansion: Amber/Crimson (230, 40, 40)
    # Regression: Sky Blue (40, 130, 240)
    color_mask = np.zeros_like(overlay)
    color_mask[shared] = [16, 185, 129]     # Emerald
    color_mask[expansion] = [239, 68, 68]    # Red / Expansion
    color_mask[regression] = [59, 130, 246]  # Blue / Difference

    alpha = 0.45
    has_annotation = shared | expansion | regression
    overlay[has_annotation] = cv2.addWeighted(
        overlay[has_annotation], 1.0 - alpha, color_mask[has_annotation], alpha, 0
    )

    # Draw contour outlines
    contours_base, _ = cv2.findContours(base_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours_foll, _ = cv2.findContours(foll_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    cv2.drawContours(overlay, contours_base, -1, (59, 130, 246), 2)  # Blue baseline outline
    cv2.drawContours(overlay, contours_foll, -1, (239, 68, 68), 2)  # Red follow-up outline

    # Convert to PIL and Base64
    pil_overlay = Image.fromarray(overlay)
    buf = io.BytesIO()
    pil_overlay.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def compare_evolution(
    followup_image: Image.Image,
    baseline_image: Optional[Image.Image] = None,
    baseline_date: Optional[str] = None,
    followup_date: Optional[str] = None,
    reported_changes: Optional[PatientReportedChanges] = None,
) -> EvolutionAssessment:
    """
    Comprehensive, medically grounded evolution assessment.
    
    Adheres strictly to the following requirements:
    1. Never invent longitudinal findings from a single photograph.
    2. Accurately detect and disclose camera angle, lighting, magnification, and blur problems.
    3. Compare shape, relative area, and color ONLY when images are sufficiently comparable.
    4. Never interpret image-processing differences as confirmed biological change.
    5. Clearly label findings as OBSERVED, REPORTED, UNCERTAIN, or NOT_ASSESSABLE.
    """
    patient_changes = reported_changes or PatientReportedChanges()

    # Case 1: Single image only (No baseline image provided)
    if baseline_image is None:
        has_reported_symptoms = any([
            patient_changes.size_change,
            patient_changes.color_change,
            patient_changes.shape_change,
            patient_changes.itching,
            patient_changes.pain,
            patient_changes.bleeding,
            patient_changes.crusting_or_oozing,
        ])

        if has_reported_symptoms:
            active_symptoms = []
            if patient_changes.size_change: active_symptoms.append("reported enlargement")
            if patient_changes.color_change: active_symptoms.append("reported darkening or color shift")
            if patient_changes.shape_change: active_symptoms.append("reported irregular shape change")
            if patient_changes.itching: active_symptoms.append("itching")
            if patient_changes.pain: active_symptoms.append("pain or tenderness")
            if patient_changes.bleeding: active_symptoms.append("spontaneous bleeding")
            if patient_changes.crusting_or_oozing: active_symptoms.append("crusting/oozing")

            summary = (
                f"Patient-reported historical changes noted ({', '.join(active_symptoms)}). "
                "Because only one photograph was uploaded, objective digital image comparison could not be performed."
            )
            return EvolutionAssessment(
                status=EvolutionProvenance.REPORTED,
                comparability=ComparabilityGrade.INCOMPATIBLE,
                baseline_date=baseline_date,
                followup_date=followup_date,
                patient_reported_changes=patient_changes,
                clinical_summary=summary,
            )

        # Purely single image with no patient-reported history
        return EvolutionAssessment(
            status=EvolutionProvenance.NOT_ASSESSABLE,
            comparability=ComparabilityGrade.INCOMPATIBLE,
            baseline_date=None,
            followup_date=followup_date,
            patient_reported_changes=patient_changes,
            clinical_summary="Single photograph snapshot. Chronological evolution over time cannot be determined without historical records or previous photographs.",
        )

    # Case 2: Pair of sequential images provided
    base_rgb = np.array(baseline_image.convert("RGB"))
    foll_rgb = np.array(followup_image.convert("RGB"))

    h_base, w_base = base_rgb.shape[:2]
    h_foll, w_foll = foll_rgb.shape[:2]

    confounders = TechnicalConfounders()
    disclosures: List[str] = []

    # Check 1: Resolution & aspect ratio
    aspect_base = w_base / float(h_base)
    aspect_foll = w_foll / float(h_foll)
    if abs(aspect_base - aspect_foll) > 0.15 or abs(w_base - w_foll) > 300 or abs(h_base - h_foll) > 300:
        confounders.resolution_mismatch = True
        disclosures.append("Images were captured at substantially different pixel resolutions or aspect ratios.")

    # Check 2: Blur / sharpness disparity
    gray_base = cv2.cvtColor(base_rgb, cv2.COLOR_RGB2GRAY)
    gray_foll = cv2.cvtColor(foll_rgb, cv2.COLOR_RGB2GRAY)
    blur_base = compute_blur_metric(gray_base)
    blur_foll = compute_blur_metric(gray_foll)
    if max(blur_base, blur_foll) > 0:
        blur_ratio = min(blur_base, blur_foll) / max(blur_base, blur_foll)
        if blur_ratio < 0.25:
            confounders.blur_difference_detected = True
            disclosures.append("One image exhibits noticeable motion blur or soft focus compared to the other.")

    # Check 3: Lighting and color distribution disparity
    color_hist_dist = compute_color_histogram_distance(base_rgb, foll_rgb)
    if color_hist_dist > 0.40:
        confounders.lighting_variation_detected = True
        disclosures.append("Marked illumination or white-balance differences detected between photo sessions.")

    # Attempt image registration & perspective alignment
    aligned_base, reg_success, inlier_ratio, reg_warnings = register_images(base_rgb, foll_rgb)
    if not reg_success:
        confounders.perspective_distortion_detected = True
        disclosures.extend(reg_warnings)

    confounders.confounding_disclosures = disclosures

    # Determine overall comparability grade
    if not reg_success:
        comparability = ComparabilityGrade.INCOMPATIBLE
    elif len(disclosures) >= 2 or inlier_ratio < 0.30:
        comparability = ComparabilityGrade.LOW
    elif len(disclosures) == 1:
        comparability = ComparabilityGrade.MODERATE
    else:
        comparability = ComparabilityGrade.HIGH

    # Compute time interval if dates are provided
    time_display = None
    if baseline_date and followup_date:
        try:
            d_base = datetime.fromisoformat(baseline_date.replace("Z", ""))
            d_foll = datetime.fromisoformat(followup_date.replace("Z", ""))
            delta_days = (d_foll - d_base).days
            if delta_days >= 365:
                years = delta_days // 365
                months = (delta_days % 365) // 30
                time_display = f"{years} yr, {months} mo interval"
            elif delta_days >= 30:
                months = delta_days // 30
                time_display = f"~{months} months interval"
            elif delta_days > 0:
                time_display = f"{delta_days} days interval"
        except Exception:
            time_display = f"{baseline_date} to {followup_date}"

    # If images are INCOMPATIBLE or comparability is LOW due to severe confounders
    if comparability in [ComparabilityGrade.INCOMPATIBLE, ComparabilityGrade.LOW]:
        summary = (
            "Sequential photographs were uploaded, but technical disparities (camera angle, lighting, or focus) "
            "prevent dependable biological delta calculation. Differences observed reflect photographic setup variations "
            "rather than confirmed tissue progression."
        )
        return EvolutionAssessment(
            status=EvolutionProvenance.UNCERTAIN,
            comparability=comparability,
            time_interval_display=time_display,
            baseline_date=baseline_date,
            followup_date=followup_date,
            patient_reported_changes=patient_changes,
            technical_confounders=confounders,
            clinical_summary=summary,
        )

    # Moderate or High Comparability: Extract Segmentations on Registered Images
    assert aligned_base is not None
    aligned_base_pil = Image.fromarray(aligned_base)
    followup_pil = followup_image

    _, _, area_base_px = segment_lesion_contour(aligned_base_pil)
    _, _, area_foll_px = segment_lesion_contour(followup_pil)

    # Extract binary masks for difference overlay
    gray_ab = cv2.cvtColor(aligned_base, cv2.COLOR_RGB2GRAY)
    gray_fo = cv2.cvtColor(foll_rgb, cv2.COLOR_RGB2GRAY)

    _, bin_ab = cv2.threshold(cv2.GaussianBlur(gray_ab, (5, 5), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if np.mean(bin_ab) > 127: bin_ab = cv2.bitwise_not(bin_ab)

    _, bin_fo = cv2.threshold(cv2.GaussianBlur(gray_fo, (5, 5), 0), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    if np.mean(bin_fo) > 127: bin_fo = cv2.bitwise_not(bin_fo)

    diff_overlay_b64 = generate_difference_overlay(foll_rgb, bin_ab, bin_fo)

    area_change_pct = None
    if area_base_px > 0:
        area_change_pct = round(((area_foll_px - area_base_px) / area_base_px) * 100.0, 1)

    color_shift = round(color_hist_dist, 3)

    # Build clinical summary
    delta_str = f"{'+' if area_change_pct and area_change_pct > 0 else ''}{area_change_pct}%" if area_change_pct is not None else "undetermined"
    summary = (
        f"Registered sequential analysis across {time_display or 'two timepoints'} revealed an apparent relative 2D area change of {delta_str}. "
        f"Alignment comparability was rated {comparability.value}."
    )
    if confounders.confounding_disclosures:
        summary += f" Technical caution: {'; '.join(confounders.confounding_disclosures)}."

    return EvolutionAssessment(
        status=EvolutionProvenance.OBSERVED,
        comparability=comparability,
        time_interval_display=time_display,
        baseline_date=baseline_date,
        followup_date=followup_date,
        patient_reported_changes=patient_changes,
        technical_confounders=confounders,
        area_change_percent=area_change_pct,
        color_shift_metric=color_shift,
        difference_overlay_base64=diff_overlay_b64,
        clinical_summary=summary,
    )
