import math
from typing import Optional, Tuple
import cv2
import numpy as np
from PIL import Image

from backend.app.schemas.measurements import (
    CalibrationPoint,
    DiameterAssessment,
    DiameterProvenance,
    RulerCalibrationResult,
)


def segment_lesion_contour(pil_image: Image.Image) -> Tuple[Optional[np.ndarray], float, float]:
    """
    Extracts the primary skin lesion contour and calculates:
    1. contour: np.ndarray of contour points
    2. feret_diameter_pixels: Maximum caliper Euclidean distance across the contour
    3. contour_area_pixels: Total pixel area of the segmented lesion
    """
    img_bgr = cv2.cvtColor(np.array(pil_image.convert("RGB")), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]

    # Pre-processing with Gaussian filter
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Otsu thresholding
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Invert if the image background is lighter than the lesion
    if np.mean(binary) > 127:
        binary = cv2.bitwise_not(binary)

    # Morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, 0.0, 0.0

    # The largest contour near the center is selected as the primary lesion
    center_x, center_y = w / 2.0, h / 2.0
    candidates = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < 100:  # Ignore microscopic noise
            continue
        m = cv2.moments(c)
        if m["m00"] > 0:
            cx = m["m10"] / m["m00"]
            cy = m["m01"] / m["m00"]
            dist_to_center = math.hypot(cx - center_x, cy - center_y)
        else:
            dist_to_center = math.hypot(c[0][0][0] - center_x, c[0][0][1] - center_y)
        candidates.append((area, -dist_to_center, c))

    if not candidates:
        return None, 0.0, 0.0

    # Pick largest, most central contour
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    primary_contour = candidates[0][2]
    contour_area = float(cv2.contourArea(primary_contour))

    # Calculate Feret's Diameter (maximum Euclidean distance on the convex hull)
    hull = cv2.convexHull(primary_contour)
    hull_pts = hull.squeeze()
    if len(hull_pts.shape) == 1 or len(hull_pts) < 2:
        # Fallback to minimum enclosing circle
        _, radius = cv2.minEnclosingCircle(primary_contour)
        return primary_contour, float(radius * 2), contour_area

    # Maximum pairwise distance on convex hull
    diffs = hull_pts[:, np.newaxis, :] - hull_pts[np.newaxis, :, :]
    dists_sq = np.sum(diffs ** 2, axis=-1)
    max_dist_pixels = float(np.sqrt(np.max(dists_sq)))

    return primary_contour, max_dist_pixels, contour_area


def calibrate_two_points(
    point1: CalibrationPoint,
    point2: CalibrationPoint,
    physical_distance_mm: float,
) -> RulerCalibrationResult:
    """
    Calculates the exact physical scale (pixels per millimeter)
    from two user-selected ruler markings.
    """
    if physical_distance_mm <= 0:
        raise ValueError("Physical distance must be strictly greater than 0 mm.")

    dx = point2.x - point1.x
    dy = point2.y - point1.y
    pixel_dist = math.hypot(dx, dy)

    if pixel_dist < 5.0:
        return RulerCalibrationResult(
            pixels_per_mm=0.0,
            pixel_distance=pixel_dist,
            physical_distance_mm=physical_distance_mm,
            is_valid=False,
            confidence_note="Selected points are too close together (<5 px) for reliable calibration.",
        )

    pixels_per_mm = pixel_dist / physical_distance_mm

    return RulerCalibrationResult(
        pixels_per_mm=round(pixels_per_mm, 4),
        pixel_distance=round(pixel_dist, 2),
        physical_distance_mm=round(physical_distance_mm, 2),
        is_valid=True,
        confidence_note=f"Calibrated scale: {pixels_per_mm:.2f} pixels/mm across {physical_distance_mm} mm.",
    )


def detect_ruler_ticks_auto(pil_image: Image.Image) -> Optional[RulerCalibrationResult]:
    """
    Optional automatic heuristic to detect high-contrast periodic millimeter tick marks.
    Returns RulerCalibrationResult if a high-confidence periodic pattern is found, else None.
    """
    img_cv = cv2.cvtColor(np.array(pil_image.convert("RGB")), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape[:2]

    # Inspect borders where rulers typically reside
    border_crops = [
        ("top", gray[: int(h * 0.25), :]),
        ("bottom", gray[int(h * 0.75) :, :]),
        ("left", gray[:, : int(w * 0.25)]),
        ("right", gray[:, int(w * 0.75) :]),
    ]

    for name, crop in border_crops:
        if crop.shape[0] < 20 or crop.shape[1] < 20:
            continue
        edges = cv2.Canny(crop, 50, 150)
        # Check projection profiles along crop axes
        profile = np.sum(edges > 0, axis=0 if "top" in name or "bottom" in name else 1)
        # Find peaks
        peaks = []
        for i in range(1, len(profile) - 1):
            if profile[i] > profile[i - 1] and profile[i] > profile[i + 1] and profile[i] > 15:
                peaks.append(i)

        if len(peaks) >= 6:
            intervals = np.diff(peaks)
            # Filter reasonable tick intervals
            median_interval = float(np.median(intervals))
            if 5.0 <= median_interval <= 100.0:
                std_interval = float(np.std(intervals))
                if std_interval < median_interval * 0.25:  # Very regular spacing
                    # Detected periodic 1mm tick marks
                    px_per_mm = median_interval
                    return RulerCalibrationResult(
                        pixels_per_mm=round(px_per_mm, 4),
                        pixel_distance=round(px_per_mm * 10, 2),
                        physical_distance_mm=10.0,
                        calibration_method=f"Automatic ruler tick detection ({name} border)",
                        is_valid=True,
                        confidence_note=f"Detected regular millimeter ruler tick marks ({median_interval:.1f} px/mm).",
                    )
    return None


def calculate_diameter_assessment(
    pil_image: Image.Image,
    calibration_result: Optional[RulerCalibrationResult] = None,
    manual_diameter_mm: Optional[float] = None,
) -> DiameterAssessment:
    """
    Calculates the complete Diameter Assessment adhering strictly to clinical rules:
    - Never uses arbitrary conversions.
    - Accurately tracks MEASURED vs USER_REPORTED vs UNAVAILABLE provenance.
    - Calculates longest Feret diameter from the verified segmentation mask.
    - Contextualizes the 6mm heuristic guideline responsibly.
    """
    contour, feret_px, area_px = segment_lesion_contour(pil_image)

    # Case 1: Calibrated Image Scale via Ruler
    if calibration_result and calibration_result.is_valid and calibration_result.pixels_per_mm > 0:
        px_per_mm = calibration_result.pixels_per_mm
        diameter_mm = round(feret_px / px_per_mm, 2)
        area_mm2 = round(area_px / (px_per_mm ** 2), 2)
        exceeds_6mm = bool(diameter_mm >= 6.0)

        return DiameterAssessment(
            status=DiameterProvenance.MEASURED,
            longest_diameter_mm=diameter_mm,
            longest_diameter_pixels=round(feret_px, 1),
            lesion_area_mm2=area_mm2,
            pixels_per_mm=round(px_per_mm, 2),
            measurement_method=calibration_result.calibration_method,
            ruler_calibration=calibration_result,
            is_exceeding_6mm_guideline=exceeds_6mm,
        )

    # Case 2: User / Patient-Reported Manual Measurement
    if manual_diameter_mm is not None and manual_diameter_mm > 0:
        exceeds_6mm = bool(manual_diameter_mm >= 6.0)
        return DiameterAssessment(
            status=DiameterProvenance.USER_REPORTED,
            longest_diameter_mm=round(manual_diameter_mm, 2),
            longest_diameter_pixels=round(feret_px, 1) if feret_px > 0 else None,
            lesion_area_mm2=None,
            pixels_per_mm=None,
            measurement_method="Patient or clinician manual caliper/ruler measurement",
            ruler_calibration=None,
            is_exceeding_6mm_guideline=exceeds_6mm,
        )

    # Case 3: Unavailable (No arbitrary conversion!)
    return DiameterAssessment(
        status=DiameterProvenance.UNAVAILABLE,
        longest_diameter_mm=None,
        longest_diameter_pixels=round(feret_px, 1) if feret_px > 0 else None,
        lesion_area_mm2=None,
        pixels_per_mm=None,
        measurement_method="Unavailable — No in-frame calibrated ruler or patient report provided",
        ruler_calibration=None,
        is_exceeding_6mm_guideline=None,
    )
