import base64
import io
import json
from fastapi import APIRouter, Form, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from PIL import Image

from backend.app.services.report_service import generate_pdf_report

router = APIRouter()


@router.post("/generate", tags=["Report"])
async def generate_pdf(
    original_file: UploadFile = File(...),
    heatmap_base64: str = Form(...),
    prediction: str = Form(...),
    confidence: float = Form(...),
    risk_level: str = Form(...),
    abcd_results_json: str = Form(...),
    ai_summary: str = Form(...),
    case_id: str = Form("Not assigned"),
    difference_base64: str = Form(None),
    diameter_detail: str = Form(None),
    evolution_detail: str = Form(None),
):
    """
    Generates an in-memory PDF clinical screening report and streams it directly to the client.
    Includes longitudinal difference overlay, diameter calibration, and evolution history when present.
    """
    try:
        orig_bytes = await original_file.read()
        orig_buf = io.BytesIO(orig_bytes)

        # Decode heatmap base64
        if "," in heatmap_base64:
            heatmap_base64 = heatmap_base64.split(",", 1)[1]
        heatmap_bytes = base64.b64decode(heatmap_base64)
        heatmap_buf = io.BytesIO(heatmap_bytes)

        # Optional difference overlay
        diff_buf = None
        if difference_base64 and len(difference_base64) > 100:
            if "," in difference_base64:
                difference_base64 = difference_base64.split(",", 1)[1]
            diff_bytes = base64.b64decode(difference_base64)
            diff_buf = io.BytesIO(diff_bytes)

        abcd_dict = json.loads(abcd_results_json)

        pdf_buf = io.BytesIO()
        generate_pdf_report(
            file_path=pdf_buf,
            original_image_path=orig_buf,
            heatmap_image_path=heatmap_buf,
            prediction=prediction,
            confidence=confidence,
            risk_level=risk_level,
            abcd_results=abcd_dict,
            ai_summary=ai_summary,
            case_id=case_id,
            difference_image_path=diff_buf,
            diameter_detail=diameter_detail,
            evolution_detail=evolution_detail,
        )
        pdf_buf.seek(0)

        filename = f"Skin_Cancer_Report_{case_id.replace('-', '_')}.pdf"
        return StreamingResponse(
            pdf_buf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")
