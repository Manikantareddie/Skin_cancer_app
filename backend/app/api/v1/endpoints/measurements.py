import io
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image

from backend.app.ml.diameter import (
    calculate_diameter_assessment,
    calibrate_two_points,
    detect_ruler_ticks_auto,
)
from backend.app.schemas.measurements import (
    CalibrationPoint,
    DiameterAssessment,
    RulerCalibrationResult,
)

router = APIRouter()


@router.post("/calibrate-ruler", response_model=DiameterAssessment, tags=["Measurements"])
async def calibrate_ruler_and_measure(
    file: UploadFile = File(...),
    p1_x: Optional[float] = Form(None),
    p1_y: Optional[float] = Form(None),
    p2_x: Optional[float] = Form(None),
    p2_y: Optional[float] = Form(None),
    physical_distance_mm: Optional[float] = Form(None),
    auto_detect: bool = Form(False),
):
    """
    Performs ruler calibration on an uploaded skin lesion photo.
    Supports:
    1. Interactive two-point ruler calibration with known millimeter spacing.
    2. Automatic tick detection heuristic when auto_detect=True.
    Returns the verified DiameterAssessment with Feret's diameter in millimeters.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid image.")

    try:
        contents = await file.read()
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not decode image: {str(e)}")

    calib_result: Optional[RulerCalibrationResult] = None

    # Option 1: Interactive two-point calibration
    if p1_x is not None and p1_y is not None and p2_x is not None and p2_y is not None and physical_distance_mm:
        try:
            pt1 = CalibrationPoint(x=p1_x, y=p1_y)
            pt2 = CalibrationPoint(x=p2_x, y=p2_y)
            calib_result = calibrate_two_points(pt1, pt2, physical_distance_mm)
        except Exception as err:
            raise HTTPException(status_code=400, detail=f"Calibration calculation failed: {str(err)}")

    # Option 2: Automatic tick detection if requested and no valid manual points provided
    elif auto_detect:
        calib_result = detect_ruler_ticks_auto(pil_image)

    return calculate_diameter_assessment(pil_image, calibration_result=calib_result)
