from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

from backend.app.schemas.measurements import (
    DiameterAssessment,
    DiameterProvenance,
    EvolutionAssessment,
    EvolutionProvenance,
    RulerCalibrationRequest,
    RulerCalibrationResult,
)


class ValidationMetrics(BaseModel):
    width: int
    height: int
    contrast: float
    skin_ratio: float
    largest_contour_ratio: float
    abnormal_region_ratio: float
    face_detected: bool
    document_like: bool


class ImageValidationResult(BaseModel):
    is_valid: bool
    reasons: List[str] = Field(default_factory=list)
    metrics: ValidationMetrics


class ABCDEIndicators(BaseModel):
    asymmetry_score: float
    asymmetry_label: str
    border_score: float
    border_label: str
    color_count: int
    color_label: str
    diameter_display: str = "Physical diameter cannot be determined from this image"
    evolution_display: str = "Not assessable — requires previous images or clinical history"
    diameter: Optional[DiameterAssessment] = None
    evolution: Optional[EvolutionAssessment] = None
    raw_dictionary: Dict[str, str] = Field(default_factory=dict)


class PredictionResult(BaseModel):
    predicted_label: Literal["Benign", "Malignant"]
    confidence_score: float
    benign_probability: float
    malignant_probability: float
    model_risk_label: Literal["LOW RISK", "MODERATE RISK", "HIGH RISK"]
    model_risk_class: Literal["low", "mid", "high"]
    qualification_note: str = "Uncalibrated research classifier output score (84.23% test accuracy, 80.89% recall)"


class ClinicalRiskResult(BaseModel):
    risk_level: Literal["LOW", "MODERATE", "HIGH"]
    risk_class: Literal["low", "mid", "high"]
    risk_score: int
    risk_reasons: List[str] = Field(default_factory=list)
    clinical_recommendation: str = "Consult a board-certified dermatologist for in-person dermoscopic evaluation."


class ObservedFeature(BaseModel):
    feature: str
    explanation: str


class StructuredAIExplanation(BaseModel):
    result_explanation: str
    observed_features: List[ObservedFeature]
    limitations: List[str]
    next_steps: List[str]


class AnalysisResponse(BaseModel):
    case_id: str
    timestamp: str
    validation: ImageValidationResult
    prediction: Optional[PredictionResult] = None
    abcde: Optional[ABCDEIndicators] = None
    clinical_risk: Optional[ClinicalRiskResult] = None
    heatmap_base64: Optional[str] = None


class ModelStatusResponse(BaseModel):
    is_loaded: bool
    model_path: Optional[str] = None
    device: str
    architecture: str
    input_size: str = "224x224"
    classes: List[str] = ["Benign", "Malignant"]


class AIExplanationRequest(BaseModel):
    case_id: Optional[str] = None
    predicted_label: str
    confidence_score: float
    risk_level: str
    abcd_results: Dict[str, str]
    diameter_assessment: Optional[DiameterAssessment] = None
    evolution_assessment: Optional[EvolutionAssessment] = None


class AIExplanationResponse(BaseModel):
    provider: str
    is_fallback: bool = False
    explanation: StructuredAIExplanation
    disclaimer: str
    error: Optional[str] = None
    # For backward compatibility with PDF reports
    clinical_summary: str = ""
    patient_guidance: str = ""
