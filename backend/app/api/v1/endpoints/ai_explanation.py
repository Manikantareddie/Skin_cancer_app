from fastapi import APIRouter
from backend.app.schemas.analysis import AIExplanationRequest, AIExplanationResponse
from backend.app.services.ai_service import generate_explanation

router = APIRouter()


@router.post("/summary", response_model=AIExplanationResponse, tags=["AI Explanation"])
def get_ai_summary(req: AIExplanationRequest):
    """
    Generates an educational clinical summary and patient guidance based on structured model findings.
    Uses NVIDIA API or Google Gemini API, with a deterministic rules-based fallback.
    Never sends raw medical images to third-party APIs.
    """
    return generate_explanation(
        predicted_label=req.predicted_label,
        confidence_score=req.confidence_score,
        risk_level=req.risk_level,
        abcd_results=req.abcd_results,
        diameter_assessment=req.diameter_assessment,
        evolution_assessment=req.evolution_assessment,
    )
