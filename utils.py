import cv2
import numpy as np
import torch
import pywt
from skimage.feature import graycomatrix, graycoprops
from torchvision import transforms

# Image transform (same as training)
image_transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

def preprocess_image(pil_image):
    """
    Input  : PIL Image
    Output : Torch tensor of shape (1, 3, 224, 224)
    """
    image = np.array(pil_image)
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    tensor = image_transform(image)
    tensor = tensor.unsqueeze(0)  # add batch dimension

    return tensor


def validate_skin_lesion_image(pil_image):
    """
    Lightweight pre-inference gate to reject obvious non-skin / non-lesion images.

    This is not a medical validator. It prevents the binary classifier from being
    forced to label unrelated images as Benign or Malignant.
    """
    image = np.array(pil_image.convert("RGB"))
    height, width = image.shape[:2]

    metrics = {
        "width": width,
        "height": height,
        "skin_ratio": 0.0,
        "largest_contour_ratio": 0.0,
        "abnormal_region_ratio": 0.0,
        "face_detected": False,
        "contrast": 0.0,
    }
    reasons = []

    if width < 128 or height < 128:
        reasons.append("Image resolution is too low for reliable lesion screening.")
        return False, reasons, metrics

    resized = cv2.resize(image, (256, 256))
    gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
    metrics["contrast"] = float(np.std(gray))

    if metrics["contrast"] < 5:
        reasons.append("Image has very low visual contrast or appears nearly blank.")

    # Skin-tone detection using two color spaces. This catches many obvious
    # non-skin uploads while still allowing a broad range of skin-like colors.
    ycrcb = cv2.cvtColor(resized, cv2.COLOR_RGB2YCrCb)
    hsv = cv2.cvtColor(resized, cv2.COLOR_RGB2HSV)

    ycrcb_mask = cv2.inRange(
        ycrcb,
        np.array([0, 125, 65], dtype=np.uint8),
        np.array([255, 185, 145], dtype=np.uint8),
    )
    hsv_mask = cv2.inRange(
        hsv,
        np.array([0, 15, 35], dtype=np.uint8),
        np.array([45, 255, 255], dtype=np.uint8),
    )
    skin_mask = cv2.bitwise_or(ycrcb_mask, hsv_mask)
    kernel = np.ones((5, 5), np.uint8)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)
    metrics["skin_ratio"] = float(np.count_nonzero(skin_mask) / skin_mask.size)

    low_skin_evidence = metrics["skin_ratio"] < 0.005

    # Reject portrait/face images. The classifier is intended for close-up
    # lesion/wound crops, not general human photos.
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    profile_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_profileface.xml"
    )
    frontal_faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(45, 45),
    )
    profile_faces = profile_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(45, 45),
    )
    faces = list(frontal_faces) + list(profile_faces)
    if len(faces) > 0:
        largest_face_area = max(w * h for (_, _, w, h) in faces)
        face_ratio = largest_face_area / float(256 * 256)
        metrics["face_detected"] = True
        if face_ratio > 0.04:
            reasons.append("A face or portrait was detected. Upload a close-up lesion or wound image only.")

    # Look for a localized dark/red lesion-like region. This blocks normal
    # face/skin photos that have skin pixels but no clear wound/lesion target.
    lab = cv2.cvtColor(resized, cv2.COLOR_RGB2LAB)
    l_channel = lab[:, :, 0]
    h_channel = hsv[:, :, 0]
    s_channel = hsv[:, :, 1]
    v_channel = hsv[:, :, 2]
    red_dominance = (
        (resized[:, :, 0].astype(np.int16) - resized[:, :, 1].astype(np.int16) > 10)
        & (resized[:, :, 0].astype(np.int16) - resized[:, :, 2].astype(np.int16) > -5)
        & (v_channel > 45)
    )
    inflamed_region = ((h_channel < 16) | (h_channel > 165)) & (s_channel > 20) & (v_channel > 45)
    brown_or_dark_region = (l_channel < np.percentile(l_channel, 35)) & (s_channel > 18)
    crust_or_scale_region = (l_channel > np.percentile(l_channel, 58)) & (s_channel > 10) & (skin_mask > 0)
    not_background = v_channel > 25
    abnormal_mask = np.where(
        (red_dominance | inflamed_region | brown_or_dark_region | crust_or_scale_region) & not_background,
        255,
        0
    ).astype(np.uint8)
    small_kernel = np.ones((3, 3), np.uint8)
    abnormal_mask = cv2.morphologyEx(abnormal_mask, cv2.MORPH_OPEN, small_kernel)
    abnormal_mask = cv2.morphologyEx(abnormal_mask, cv2.MORPH_CLOSE, kernel)

    abnormal_contours, _ = cv2.findContours(
        abnormal_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if abnormal_contours:
        abnormal_area = max(cv2.contourArea(c) for c in abnormal_contours)
        metrics["abnormal_region_ratio"] = float(abnormal_area / (256 * 256))

    # A lesion image should usually contain a meaningful candidate region.
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    candidates = [binary, cv2.bitwise_not(binary)]
    largest_ratio = 0.0
    for candidate in candidates:
        contours, _ = cv2.findContours(
            candidate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        for contour in contours:
            contour_ratio = cv2.contourArea(contour) / float(256 * 256)
            if 0.003 <= contour_ratio <= 0.90:
                largest_ratio = max(largest_ratio, contour_ratio)

    metrics["largest_contour_ratio"] = float(largest_ratio)

    has_lesion_evidence = (
        metrics["abnormal_region_ratio"] >= 0.0001
        or 0.001 <= largest_ratio <= 0.90
        or (
            metrics["skin_ratio"] >= 0.08
            and metrics["contrast"] >= 10
            and not metrics["face_detected"]
        )
    )

    if low_skin_evidence and not has_lesion_evidence:
        reasons.append("Image does not appear to contain enough skin or lesion-region evidence.")

    if not has_lesion_evidence:
        reasons.append("No localized wound or lesion-like region was detected.")

    return len(reasons) == 0, reasons, metrics



def extract_texture_features(pil_image):
    """
    Input  : PIL Image
    Output : Torch tensor of shape (1, 12)
    """
    image = np.array(pil_image)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # ---- GLCM FEATURES (4) ----
    glcm = graycomatrix(
        gray,
        distances=[1],
        angles=[0],
        levels=256,
        symmetric=True,
        normed=True
    )

    contrast = graycoprops(glcm, 'contrast')[0, 0]
    homogeneity = graycoprops(glcm, 'homogeneity')[0, 0]
    energy = graycoprops(glcm, 'energy')[0, 0]
    correlation = graycoprops(glcm, 'correlation')[0, 0]

    glcm_features = [contrast, homogeneity, energy, correlation]

    # ---- WAVELET FEATURES (8) ----
    coeffs = pywt.dwt2(gray, 'haar')
    cA, (cH, cV, cD) = coeffs

    wavelet_features = [
        np.mean(cA), np.std(cA),
        np.mean(cH), np.std(cH),
        np.mean(cV), np.std(cV),
        np.mean(cD), np.std(cD)
    ]

    features = glcm_features + wavelet_features

    features = torch.tensor(features, dtype=torch.float32)
    return features.unsqueeze(0)  # shape (1, 12)

def compute_asymmetry(pil_image):
    """
    Computes asymmetry score for a skin lesion.
    Output: float value between 0 and 1
    """

    # Convert to grayscale
    image = np.array(pil_image)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Resize to fixed size for consistency
    gray = cv2.resize(gray, (256, 256))

    # Normalize
    gray = gray.astype("float32") / 255.0

    # Split into left and right halves
    left_half = gray[:, :128]
    right_half = gray[:, 128:]

    # Flip right half for comparison
    right_half_flipped = np.fliplr(right_half)

    # Compute absolute difference
    diff = np.abs(left_half - right_half_flipped)

    # Mean difference = asymmetry
    asymmetry_score = np.mean(diff)

    # Clip to [0,1] safety
    asymmetry_score = float(np.clip(asymmetry_score, 0.0, 1.0))

    return asymmetry_score


def compute_border_irregularity(pil_image):
    """
    Computes border irregularity score using contour compactness.
    Returns a float value.
    """

    image = np.array(pil_image)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    # Resize for consistency
    gray = cv2.resize(gray, (256, 256))

    # Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Otsu threshold to segment lesion
    _, binary = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    # Invert if background is white
    if np.mean(binary) > 127:
        binary = cv2.bitwise_not(binary)

    # Find contours
    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if len(contours) == 0:
        return 0.0

    # Largest contour = lesion
    contour = max(contours, key=cv2.contourArea)

    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)

    if area == 0:
        return 0.0

    # Compactness / irregularity index
    irregularity = (perimeter ** 2) / (4 * np.pi * area)

    return float(irregularity)


import cv2
import numpy as np

def compute_color_variation(pil_image, k=3):
    """
    Returns number of dominant colors using KMeans clustering
    """
    img = np.array(pil_image)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Resize for speed & stability
    img = cv2.resize(img, (200, 200))
    pixels = img.reshape((-1, 3)).astype(np.float32)

    # KMeans clustering
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(
        pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS
    )

    return len(centers)


def compute_diameter(pil_image):
    """
    Estimates lesion diameter in millimeters (AI-estimated).
    Returns diameter_mm (float)
    """

    image = np.array(pil_image)
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, (256, 256))

    # Blur & threshold
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )

    if np.mean(binary) > 127:
        binary = cv2.bitwise_not(binary)

    contours, _ = cv2.findContours(
        binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if len(contours) == 0:
        return 0.0

    contour = max(contours, key=cv2.contourArea)

    # Minimum enclosing circle
    (x, y), radius = cv2.minEnclosingCircle(contour)
    diameter_pixels = radius * 2

    # Approximate conversion (assumption: 1 pixel ≈ 0.05 mm)
    diameter_mm = diameter_pixels * 0.05

    return round(float(diameter_mm), 2)


def compute_evolution_score(
    asymmetry_score,
    border_score,
    color_count
):
    """
    Estimates evolution risk based on ABC instability.
    Returns (score, label)
    """

    score = 0

    # Asymmetry contribution
    if asymmetry_score > 0.5:
        score += 1

    # Border contribution
    if border_score > 2.0:
        score += 1

    # Color contribution
    if color_count >= 3:
        score += 1

    # Interpret score
    if score == 0:
        return score, "Stable"
    elif score == 1:
        return score, "Mild Change"
    elif score == 2:
        return score, "Moderate Change"
    else:
        return score, "Progressive Change"
