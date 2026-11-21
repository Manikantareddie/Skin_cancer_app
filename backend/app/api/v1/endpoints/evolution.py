import io
import json
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image

from backend.app.ml.evolution import compare_evolution
from backend.app.schemas.measurements import EvolutionAssessment, PatientReportedChanges

router = APIRouter()


@router.post("/compare", response_model=EvolutionAssessment, tags=["Evolution"])
async def compare_lesion_evolution(
    followup_file: UploadFile = File(...),
    baseline_file: Optional[UploadFile] = File(None),
    baseline_date: Optional[str] = Form(None),
    followup_date: Optional[str] = Form(None),
    patient_reported_json: Optional[str] = Form(None),
):
    """
    Evaluates longitudinal evolution between two sequential skin lesion captures.
    Adheres strictly to medical safety:
    - Never invents findings from a single image.
    - Accurately detects and discloses technical confounders (lighting, perspective, blur).
    - Compares morphology only when images are sufficiently comparable.
    - Labels changes as OBSERVED, REPORTED, UNCERTAIN, or NOT_ASSESSABLE.
    """
    if not followup_file.content_type or not followup_file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Follow-up file must be a valid image.")

    try:
        contents = await followup_file.read()
        followup_img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not decode follow-up image: {str(e)}")

    baseline_img = None
    if baseline_file:
        try:
            b_contents = await baseline_file.read()
            baseline_img = Image.open(io.BytesIO(b_contents)).convert("RGB")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not decode baseline image: {str(e)}")

    reported_changes = PatientReportedChanges()
    if patient_reported_json:
        try:
            data = json.loads(patient_reported_json)
            reported_changes = PatientReportedChanges.model_validate(data)
        except Exception:
            pass

    return compare_evolution(
        followup_image=followup_img,
        baseline_image=baseline_img,
        baseline_date=baseline_date,
        followup_date=followup_date,
        reported_changes=reported_changes,
    )
