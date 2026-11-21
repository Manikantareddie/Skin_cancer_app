import io
import json
import logging
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image

from backend.app.ml.diameter import (
    calculate_diameter_assessment,
    calibrate_two_points,
)
from backend.app.ml.evolution import compare_evolution
from backend.app.schemas.analysis import AnalysisResponse
from backend.app.schemas.measurements import (
    CalibrationPoint,
    PatientReportedChanges,
    RulerCalibrationResult,
)
from backend.app.services.clinical_service import (
    evaluate_clinical_risk,
    extract_abcde_indicators,
    validate_image,
)
from backend.app.services.model_service import model_service

logger = logging.getLogger("skin_cancer_backend")
router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse, tags=["Inference"])
async def analyze_lesion_image(
    file: UploadFile = File(...),
    baseline_file: Optional[UploadFile] = File(None),
    baseline_date: Optional[str] = Form(None),
    followup_date: Optional[str] = Form(None),
    manual_diameter_mm: Optional[float] = Form(None),
    p1_x: Optional[float] = Form(None),
    p1_y: Optional[float] = Form(None),
    p2_x: Optional[float] = Form(None),
    p2_y: Optional[float] = Form(None),
    physical_distance_mm: Optional[float] = Form(None),
    patient_reported_json: Optional[str] = Form(None),
):
    """
    Complete multimodal screening pipeline with functional Diameter and Evolution:
    1. Validates uploaded primary lesion image.
    2. Runs clinical pre-inference validation gate (skin context, contrast, face detection).
    3. If valid, processes ruler calibration or manual diameter input (never arbitrary).
    4. Evaluates longitudinal evolution if baseline image or patient history is provided.
    5. Computes ABCDE morphological criteria and 12-feature texture vector.
    6. Runs ResNet-18 + Texture fusion PyTorch inference and Grad-CAM.
    7. Evaluates composite clinical priority incorporating validated D and E findings.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid image (PNG, JPG, JPEG).")

    try:
        contents = await file.read()
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not decode image: {str(e)}")

    baseline_img = None
    if baseline_file:
        try:
            b_contents = await baseline_file.read()
            baseline_img = Image.open(io.BytesIO(b_contents)).convert("RGB")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not decode baseline image: {str(e)}")

    case_id = f"SKIN-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    timestamp = datetime.utcnow().isoformat() + "Z"

    try:
        # Step 1: Pre-inference Image Validation Gate
        validation_result = validate_image(pil_image)

        if not validation_result.is_valid:
            return AnalysisResponse(
                case_id=case_id,
                timestamp=timestamp,
                validation=validation_result,
                prediction=None,
                abcde=None,
                clinical_risk=None,
                heatmap_base64=None,
            )

        # Step 2: Diameter Assessment
        calib_result: Optional[RulerCalibrationResult] = None
        if p1_x is not None and p1_y is not None and p2_x is not None and p2_y is not None and physical_distance_mm:
            try:
                pt1 = CalibrationPoint(x=p1_x, y=p1_y)
                pt2 = CalibrationPoint(x=p2_x, y=p2_y)
                calib_result = calibrate_two_points(pt1, pt2, physical_distance_mm)
            except Exception:
                pass

        diameter_eval = calculate_diameter_assessment(
            pil_image,
            calibration_result=calib_result,
            manual_diameter_mm=manual_diameter_mm,
        )

        # Step 3: Evolution Assessment
        reported_changes = PatientReportedChanges()
        if patient_reported_json:
            try:
                data = json.loads(patient_reported_json)
                reported_changes = PatientReportedChanges.model_validate(data)
            except Exception:
                pass

        evolution_eval = compare_evolution(
            followup_image=pil_image,
            baseline_image=baseline_img,
            baseline_date=baseline_date,
            followup_date=followup_date,
            reported_changes=reported_changes,
        )

        # Step 4: ABCDE Feature Extraction with validated D and E
        abcde_indicators = extract_abcde_indicators(
            pil_image,
            diameter_assessment=diameter_eval,
            evolution_assessment=evolution_eval,
        )

        # Step 5: ResNet + Texture Fusion Inference and Grad-CAM
        prediction_result, heatmap_base64, _ = model_service.predict(pil_image)

        # Step 6: Multi-factorial Clinical Risk Evaluation
        clinical_risk = evaluate_clinical_risk(
            abcde_indicators,
            prediction_result.predicted_label,
            prediction_result.confidence_score,
        )

        return AnalysisResponse(
            case_id=case_id,
            timestamp=timestamp,
            validation=validation_result,
            prediction=prediction_result,
            abcde=abcde_indicators,
            clinical_risk=clinical_risk,
            heatmap_base64=heatmap_base64,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"Unexpected error during lesion analysis pipeline: {exc}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while analyzing the lesion image. Please ensure the image is clear and try again.",
        )
