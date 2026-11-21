from pathlib import Path
from PIL import Image
import numpy as np
import pytest

from backend.app.services.clinical_service import (
    evaluate_clinical_risk,
    extract_abcde_indicators,
    validate_image,
)
from backend.app.schemas.analysis import ABCDEIndicators


def test_validation_gate_rejects_blank():
    blank_img = Image.fromarray(np.ones((256, 256, 3), dtype=np.uint8) * 255)
    val = validate_image(blank_img)
    assert not val.is_valid
    assert len(val.reasons) > 0


def test_validation_gate_accepts_synthetic_lesion():
    sample_path = Path("data/samples/sample_lesion.png")
    assert sample_path.exists(), "Sample lesion image should exist"
    img = Image.open(sample_path)
    val = validate_image(img)
    assert val.is_valid
    assert len(val.reasons) == 0


def test_extract_abcde_indicators():
    img = Image.open("data/samples/sample_lesion.png")
    abcde = extract_abcde_indicators(img)
    assert 0.0 <= abcde.asymmetry_score <= 1.0
    assert abcde.border_score >= 0.0
    assert abcde.color_count >= 1
    assert abcde.diameter_mm >= 0.0
    assert abcde.evolution_score in [0, 1, 2, 3]


def test_evaluate_clinical_risk():
    img = Image.open("data/samples/sample_lesion.png")
    abcde = extract_abcde_indicators(img)
    risk_low = evaluate_clinical_risk(abcde, "Benign", 95.0)
    assert risk_low.risk_level in ["LOW", "MODERATE", "HIGH"]

    risk_high = evaluate_clinical_risk(abcde, "Malignant", 85.0)
    assert risk_high.risk_score >= 2
