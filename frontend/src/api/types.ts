export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  timestamp: string;
}

export interface ModelStatusResponse {
  is_loaded: boolean;
  model_path: string | null;
  device: string;
  architecture: string;
  input_size: string;
  classes: string[];
}

export interface ValidationMetrics {
  width: number;
  height: number;
  contrast: number;
  skin_ratio: number;
  largest_contour_ratio: number;
  abnormal_region_ratio: number;
  face_detected: boolean;
  document_like: boolean;
}

export interface ImageValidationResult {
  is_valid: boolean;
  reasons: string[];
  metrics: ValidationMetrics;
}

export interface PredictionResult {
  predicted_label: 'Benign' | 'Malignant';
  confidence_score: number;
  benign_probability: number;
  malignant_probability: number;
  model_risk_label: 'LOW RISK' | 'MODERATE RISK' | 'HIGH RISK';
  model_risk_class: 'low' | 'mid' | 'high';
  qualification_note?: string;
}

export type DiameterProvenance = 'MEASURED' | 'USER_REPORTED' | 'UNAVAILABLE';
export type EvolutionProvenance = 'OBSERVED' | 'REPORTED' | 'UNCERTAIN' | 'NOT_ASSESSABLE';
export type ComparabilityGrade = 'HIGH' | 'MODERATE' | 'LOW' | 'INCOMPATIBLE';

export interface CalibrationPoint {
  x: number;
  y: number;
}

export interface RulerCalibrationResult {
  pixels_per_mm: number;
  pixel_distance: number;
  physical_distance_mm: number;
  calibration_method: string;
  is_valid: boolean;
  confidence_note: string;
}

export interface DiameterAssessment {
  status: DiameterProvenance;
  longest_diameter_mm?: number | null;
  longest_diameter_pixels?: number | null;
  lesion_area_mm2?: number | null;
  pixels_per_mm?: number | null;
  measurement_method: string;
  ruler_calibration?: RulerCalibrationResult | null;
  guideline_note: string;
  is_exceeding_6mm_guideline?: boolean | null;
}

export interface PatientReportedChanges {
  size_change: boolean;
  color_change: boolean;
  shape_change: boolean;
  itching: boolean;
  pain: boolean;
  bleeding: boolean;
  crusting_or_oozing: boolean;
  patient_notes?: string | null;
}

export interface TechnicalConfounders {
  lighting_variation_detected: boolean;
  perspective_distortion_detected: boolean;
  resolution_mismatch: boolean;
  blur_difference_detected: boolean;
  confounding_disclosures: string[];
}

export interface EvolutionAssessment {
  status: EvolutionProvenance;
  comparability: ComparabilityGrade;
  time_interval_display?: string | null;
  baseline_date?: string | null;
  followup_date?: string | null;
  patient_reported_changes: PatientReportedChanges;
  technical_confounders: TechnicalConfounders;
  area_change_percent?: number | null;
  shape_asymmetry_delta?: number | null;
  color_shift_metric?: number | null;
  difference_overlay_base64?: string | null;
  clinical_summary: string;
  biological_change_warning: string;
}

export interface ABCDEIndicators {
  asymmetry_score: number;
  asymmetry_label: string;
  border_score: number;
  border_label: string;
  color_count: number;
  color_label: string;
  diameter_display: string;
  evolution_display: string;
  diameter?: DiameterAssessment | null;
  evolution?: EvolutionAssessment | null;
  raw_dictionary: Record<string, string>;
}

export interface ClinicalRiskResult {
  risk_level: 'LOW' | 'MODERATE' | 'HIGH';
  risk_class: 'low' | 'mid' | 'high';
  risk_score: number;
  risk_reasons: string[];
  clinical_recommendation: string;
}

export interface AnalysisResponse {
  case_id: string;
  timestamp: string;
  validation: ImageValidationResult;
  prediction?: PredictionResult;
  abcde?: ABCDEIndicators;
  clinical_risk?: ClinicalRiskResult;
  heatmap_base64?: string;
}

export interface AIExplanationRequest {
  case_id?: string;
  predicted_label: string;
  confidence_score: number;
  risk_level: string;
  abcd_results: Record<string, string>;
  diameter_assessment?: DiameterAssessment | null;
  evolution_assessment?: EvolutionAssessment | null;
}

export interface ObservedFeature {
  feature: string;
  explanation: string;
}

export interface StructuredAIExplanation {
  result_explanation: string;
  observed_features: ObservedFeature[];
  limitations: string[];
  next_steps: string[];
}

export interface AIExplanationResponse {
  provider: string;
  is_fallback?: boolean;
  explanation: StructuredAIExplanation;
  disclaimer: string;
  clinical_summary?: string;
  patient_guidance?: string;
  error?: string | null;
}
