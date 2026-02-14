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
