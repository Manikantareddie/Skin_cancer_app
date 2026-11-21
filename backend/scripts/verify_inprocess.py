"""In-process end-to-end verification of all ML, clinical, AI, and report services."""
import io
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from PIL import Image
from backend.app.services.model_service import model_service
from backend.app.services.clinical_service import extract_abcde_indicators, evaluate_clinical_risk
from backend.app.services.ai_service import generate_explanation
from backend.app.services.report_service import generate_pdf_report


def run_verification():
    print("=== DERMAASSIST FULL WORKFLOW IN-PROCESS VERIFICATION ===")

    sample_path = project_root / "data" / "samples" / "sample_lesion.png"
    assert sample_path.exists(), f"Sample image not found: {sample_path}"
    print(f"1. Loading sample image: {sample_path.name}")
    img = Image.open(sample_path).convert("RGB")

    # Step 1: Model Prediction & Grad-CAM
    print("\n2. Executing Real ResNet18 + Texture Model Inference & Grad-CAM...")
    model_status = model_service.get_status()
    print(f"   Model Loaded: {model_status.is_loaded}")
    print(f"   Architecture: {model_status.architecture}")
    print(f"   Classes: {model_status.classes}")

    pred, heatmap_data_url, heatmap_pil = model_service.predict(img)
    print(f"   -> Predicted Class: {pred.predicted_label}")
    print(f"   -> Output Score: {pred.confidence_score:.2f}%")
    print(f"   -> Heatmap Generated: {bool(heatmap_data_url and len(heatmap_data_url) > 100)}")

    # Step 2: ABCDE & Clinical Risk Evaluation
    print("\n3. Calculating Scientifically Accurate ABCDE Morphological Indicators...")
    abcde = extract_abcde_indicators(img)
    risk = evaluate_clinical_risk(abcde, pred.predicted_label, pred.confidence_score)
    print(f"   -> Asymmetry: {abcde.asymmetry_label} (Score: {abcde.asymmetry_score:.2f})")
    print(f"   -> Border: {abcde.border_label} (Score: {abcde.border_score:.2f})")
    print(f"   -> Color Clusters: {abcde.color_count} ({abcde.color_label})")
    print(f"   -> Diameter: {abcde.raw_dictionary.get('D – Diameter')}")
    print(f"   -> Evolution: {abcde.raw_dictionary.get('E – Evolution')}")
    print(f"   -> Clinical Priority: {risk.risk_level}")

    assert "cannot be determined" in abcde.raw_dictionary.get("D – Diameter", "").lower(), "Diameter must state cannot be determined"
    assert "not assessable" in abcde.raw_dictionary.get("E – Evolution", "").lower(), "Evolution must state not assessable"

    # Step 3: Structured AI Explanation Generation
    print("\n4. Testing Structured AI Explanation Generation (NVIDIA NIM / Fallback)...")
    ai_resp = generate_explanation(
        predicted_label=pred.predicted_label,
        confidence_score=pred.confidence_score,
        risk_level=risk.risk_level,
        abcd_results=abcde.raw_dictionary,
    )
    print(f"   -> Provider: {ai_resp.provider} (Fallback: {ai_resp.is_fallback})")
    print(f"   -> Result Explanation: {ai_resp.explanation.result_explanation[:100]}...")
    print(f"   -> Observed Features: {len(ai_resp.explanation.observed_features)}")
    for f in ai_resp.explanation.observed_features:
        print(f"      • {f.feature}: {f.explanation[:60]}...")
    print(f"   -> Limitations Count: {len(ai_resp.explanation.limitations)}")
    print(f"   -> Next Steps Count: {len(ai_resp.explanation.next_steps)}")
    if ai_resp.error:
        print(f"   -> Engine Note: {ai_resp.error[:100]}")

    # Step 4: PDF Report Generation
    print("\n5. Testing PDF Report Compilation with ReportLab...")
    pdf_out = project_root / "data" / "samples" / "test_verification_report.pdf"
    heatmap_buf = io.BytesIO()
    heatmap_pil.save(heatmap_buf, format="PNG")
    heatmap_buf.seek(0)

    orig_buf = io.BytesIO()
    img.save(orig_buf, format="PNG")
    orig_buf.seek(0)

    summary_text = f"Result: {ai_resp.explanation.result_explanation}\n\n" + "\n".join(
        f"• {f.feature}: {f.explanation}" for f in ai_resp.explanation.observed_features
    )

    generate_pdf_report(
        file_path=str(pdf_out),
        original_image_path=orig_buf,
        heatmap_image_path=heatmap_buf,
        prediction=pred.predicted_label,
        confidence=pred.confidence_score,
        risk_level=risk.risk_level,
        abcd_results=abcde.raw_dictionary,
        ai_summary=summary_text,
        case_id="VERIFY-TEST-001",
    )
    assert pdf_out.exists() and pdf_out.stat().st_size > 1000, "PDF must exist and be > 1KB"
    print(f"   -> PDF successfully generated at {pdf_out.name} ({pdf_out.stat().st_size} bytes)")

    print("\n[SUCCESS] ALL VERIFICATION CHECKS PASSED PERFECTLY!")


if __name__ == "__main__":
    run_verification()
