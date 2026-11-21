from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DiameterProvenance(str, Enum):
    MEASURED = "MEASURED"                    # Calibrated image scale via ruler
    USER_REPORTED = "USER_REPORTED"          # Manually entered by patient or clinician
    UNAVAILABLE = "UNAVAILABLE"              # Neither calibrated scale nor user input


class EvolutionProvenance(str, Enum):
    OBSERVED = "OBSERVED"                    # Quantitative delta from comparable registered image pair
    REPORTED = "REPORTED"                    # Documented purely from patient-reported history / symptoms
    UNCERTAIN = "UNCERTAIN"                  # Confounding factors (lighting, angle, zoom) prevent confirmation
    NOT_ASSESSABLE = "NOT_ASSESSABLE"        # Single image only; no prior images or longitudinal history


class ComparabilityGrade(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    INCOMPATIBLE = "INCOMPATIBLE"


class CalibrationPoint(BaseModel):
    x: float
    y: float


class RulerCalibrationRequest(BaseModel):
    point1: CalibrationPoint
    point2: CalibrationPoint
    physical_distance_mm: float = Field(..., gt=0.0, description="Known physical distance in mm (e.g. 10mm)")


class RulerCalibrationResult(BaseModel):
    pixels_per_mm: float
    pixel_distance: float
    physical_distance_mm: float
    calibration_method: str = "Interactive two-point ruler calibration"
    is_valid: bool = True
    confidence_note: str = ""


class DiameterAssessment(BaseModel):
    status: DiameterProvenance
    longest_diameter_mm: Optional[float] = None
    longest_diameter_pixels: Optional[float] = None
    lesion_area_mm2: Optional[float] = None
    pixels_per_mm: Optional[float] = None
    measurement_method: str = "Unavailable"
    ruler_calibration: Optional[RulerCalibrationResult] = None
    guideline_note: str = (
        "Clinical Reference Note: While lesions exceeding 6 mm warrant heightened clinical scrutiny under the ABCDE criteria, "
        "diameter alone is not a definitive diagnostic boundary. Small melanomas (<6 mm) can occur, and many benign nevi exceed 6 mm."
    )
    is_exceeding_6mm_guideline: Optional[bool] = None


class PatientReportedChanges(BaseModel):
    size_change: bool = False
    color_change: bool = False
    shape_change: bool = False
    itching: bool = False
    pain: bool = False
    bleeding: bool = False
    crusting_or_oozing: bool = False
    patient_notes: Optional[str] = None


class TechnicalConfounders(BaseModel):
    lighting_variation_detected: bool = False
    perspective_distortion_detected: bool = False
    resolution_mismatch: bool = False
    blur_difference_detected: bool = False
    confounding_disclosures: List[str] = Field(default_factory=list)


class EvolutionAssessment(BaseModel):
    status: EvolutionProvenance
    comparability: ComparabilityGrade = ComparabilityGrade.INCOMPATIBLE
    time_interval_display: Optional[str] = None
    baseline_date: Optional[str] = None
    followup_date: Optional[str] = None
    patient_reported_changes: PatientReportedChanges = Field(default_factory=PatientReportedChanges)
    technical_confounders: TechnicalConfounders = Field(default_factory=TechnicalConfounders)
    area_change_percent: Optional[float] = None
    shape_asymmetry_delta: Optional[float] = None
    color_shift_metric: Optional[float] = None
    difference_overlay_base64: Optional[str] = None
    clinical_summary: str = "Single photographic snapshot; chronological evolution is not assessable."
    biological_change_warning: str = (
        "Automated alignment detects pixel and contour variations. Variations may stem from lighting, camera angle, "
        "or image focus, and must not be interpreted as confirmed biological pathology without dermatological examination."
    )
