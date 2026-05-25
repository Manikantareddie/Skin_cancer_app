# ============================================================
# AI SKIN CANCER DETECTION SYSTEM
# Final Year Project | AI & Data Science
# ============================================================
import streamlit as st
import torch
import os
import uuid
from datetime import datetime


from huggingface_hub import hf_hub_download

from PIL import Image



# ---------------- AI & MODEL IMPORTS ----------------
from model import ResNetTextureFusion
from utils import (
    preprocess_image,
    validate_skin_lesion_image,
    extract_texture_features,
    compute_asymmetry,
    compute_border_irregularity,
    compute_color_variation,
    compute_diameter,
    compute_evolution_score
)

from gradcam import GradCAM, overlay_heatmap_on_image
from ai_engine import generate_ai_summary
from report_generator import generate_pdf_report

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="AI Skin Cancer Detection",
    page_icon="🔬",
    layout="wide"
)

if "ai_response" not in st.session_state:
    st.session_state.ai_response = "AI summary not generated yet."
if "patient_guidance" not in st.session_state:
    st.session_state.patient_guidance = None




# ============================================================
# GLOBAL CLINICAL UI (LIGHT • CLEAN • PROFESSIONAL)
# ============================================================
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: Inter, "Segoe UI", sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(20, 184, 166, .16), transparent 28rem),
        radial-gradient(circle at top right, rgba(56, 189, 248, .17), transparent 30rem),
        linear-gradient(180deg, #f0fbff 0%, #f8fcf9 46%, #f7fbff 100%);
    color: #1f2937;
}

.stApp > header {
    visibility: hidden;
}

.stDeployButton, #MainMenu, footer {
    visibility: hidden;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f766e 0%, #164e63 100%);
}

[data-testid="stSidebar"] * {
    color: #f8fafc !important;
}

[data-testid="stSidebar"] .stMarkdown p {
    color: #dff7f3 !important;
}

.block-container {
    max-width: 1240px;
    padding: 1rem 1.25rem 2rem;
}

h1, h2, h3 {
    color: #16324f;
    letter-spacing: 0;
}

h1 {
    font-size: clamp(1.55rem, 2vw, 2.15rem);
    line-height: 1.15;
    margin: 0;
}

p, li {
    color: #51677b;
    font-size: .94rem;
    line-height: 1.55;
}

.app-topbar {
    background: linear-gradient(135deg, #ffffff 0%, #f0fdfa 62%, #ecfeff 100%);
    border: 1px solid #bfe6df;
    border-left: 6px solid #14b8a6;
    border-radius: 8px;
    padding: 1rem 1.1rem;
    margin-bottom: .85rem;
    box-shadow: 0 10px 26px rgba(16, 42, 67, .07);
}

.eyebrow {
    color: #0f766e;
    font-size: .76rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .08em;
    margin-bottom: .25rem;
}

.topbar-row {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: flex-end;
}

.topbar-copy {
    color: #587083;
    margin: .42rem 0 0;
    max-width: 760px;
}

.chip-row {
    display: flex;
    gap: .45rem;
    flex-wrap: wrap;
    justify-content: flex-end;
}

.chip {
    background: #ffffff;
    color: #0f766e;
    border: 1px solid #99f6e4;
    border-radius: 999px;
    padding: .32rem .58rem;
    font-size: .78rem;
    font-weight: 750;
}

.compact-card, .card {
    background: #ffffff;
    border: 1px solid #cfe4ee;
    border-radius: 8px;
    padding: 1rem;
    margin: .75rem 0;
    box-shadow: 0 1px 2px rgba(16, 42, 67, .04);
}

.tool-card {
    background: linear-gradient(180deg, #ffffff 0%, #f8fffd 100%);
    border: 1px solid #c7eadf;
    border-radius: 8px;
    padding: 1rem;
    min-height: 226px;
    box-shadow: 0 1px 2px rgba(16, 42, 67, .04);
}

.report-panel {
    background: linear-gradient(135deg, #ecfeff 0%, #f0fdfa 100%);
    border: 1px solid #99f6e4;
    border-radius: 8px;
    padding: 1rem;
    margin-top: .9rem;
}

.report-title {
    color: #164e63;
    font-size: 1.15rem;
    font-weight: 850;
    margin: 0 0 .25rem;
}

.report-checklist {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: .55rem;
    margin-top: .75rem;
}

.report-check-item {
    background: rgba(255, 255, 255, .72);
    border: 1px solid #c7eadf;
    border-radius: 8px;
    color: #164e63;
    font-size: .84rem;
    font-weight: 750;
    padding: .55rem .65rem;
}

.sidebar-brand {
    padding: .6rem 0 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, .25);
    margin-bottom: 1rem;
}

.sidebar-brand-title {
    font-size: 1.1rem;
    font-weight: 850;
    line-height: 1.2;
}

.sidebar-brand-subtitle {
    font-size: .82rem;
    opacity: .86;
    margin-top: .35rem;
}

.section-title {
    color: #16324f;
    font-size: 1rem;
    font-weight: 700;
    margin: 0 0 .45rem;
}

.step-list {
    display: grid;
    gap: .55rem;
    margin-top: .85rem;
}

.step-item {
    display: flex;
    align-items: center;
    gap: .65rem;
    color: #3b5267;
    font-size: .9rem;
}

.step-dot {
    width: 1.55rem;
    height: 1.55rem;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: #ccfbf1;
    color: #0f766e;
    font-weight: 800;
    font-size: .76rem;
    flex: 0 0 auto;
}

.card h3 {
    font-size: 1rem;
    line-height: 1.25;
    margin: 0 0 .55rem;
}

.card p {
    margin: .28rem 0;
}

.muted {
    color: #6b7f92;
    margin: 0;
}

.metric-card {
    background: #ffffff;
    border: 1px solid #cfe4ee;
    border-radius: 8px;
    padding: .85rem;
    min-height: 92px;
}

.metric-label {
    color: #6b7f92;
    font-size: .78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .04em;
    margin-bottom: .25rem;
}

.metric-value {
    color: #16324f;
    font-size: 1.18rem;
    font-weight: 750;
    line-height: 1.2;
}

.risk-meter-card {
    background: #ffffff;
    border: 1px solid #cfe4ee;
    border-radius: 8px;
    padding: 1rem;
    margin: .75rem 0;
}

.risk-meter-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: .65rem;
}

.risk-meter-title {
    color: #16324f;
    font-size: 1rem;
    font-weight: 800;
}

.risk-meter-value {
    color: #334155;
    font-size: .9rem;
    font-weight: 750;
}

.probability-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: .75rem;
    margin: .75rem 0;
}

.probability-card {
    background: #ffffff;
    border: 1px solid #cfe4ee;
    border-radius: 8px;
    padding: .85rem;
}

.probability-label {
    color: #64748b;
    font-size: .78rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .04em;
}

.probability-value {
    color: #16324f;
    font-size: 1.45rem;
    font-weight: 850;
    line-height: 1.15;
    margin-top: .25rem;
}

.quality-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: .65rem;
    margin: .75rem 0;
}

.quality-card {
    background: #ffffff;
    border: 1px solid #cfe4ee;
    border-radius: 8px;
    padding: .75rem;
}

.quality-label {
    color: #64748b;
    font-size: .72rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: .04em;
}

.quality-value {
    color: #16324f;
    font-size: 1rem;
    font-weight: 850;
    margin-top: .2rem;
}

@media (max-width: 768px) {
    .probability-grid, .quality-grid {
        grid-template-columns: 1fr;
    }
}

.badge {
    display: inline-flex;
    align-items: center;
    padding: .38rem .72rem;
    border-radius: 999px;
    font-weight: 750;
    font-size: .82rem;
}

.low {
    background: #e8f7ef;
    color: #176c4f;
}

.mid {
    background: #fff4d8;
    color: #8a5b00;
}

.high {
    background: #fde8e8;
    color: #a61b1b;
}

.result-list {
    margin: .65rem 0 0;
    padding-left: 1.05rem;
}

.result-list li {
    margin-bottom: .25rem;
}

.stImage img {
    border-radius: 8px;
    border: 1px solid #cfe4ee;
    max-height: 440px;
    object-fit: contain;
}

.stFileUploader section {
    border: 1px dashed #22b8a7;
    border-radius: 8px;
    background: #f8fffd;
    padding: .85rem;
}

.stButton > button, .stDownloadButton > button {
    width: 100%;
    border-radius: 8px;
    border: 1px solid #0e7490;
    background: linear-gradient(135deg, #0891b2 0%, #14b8a6 100%);
    color: #ffffff !important;
    padding: .72rem 1rem;
    font-weight: 800;
    box-shadow: 0 8px 18px rgba(14, 116, 144, .18);
    transition: transform .12s ease, box-shadow .12s ease, filter .12s ease;
}

.stButton > button:hover, .stDownloadButton > button:hover {
    border-color: #155e75;
    background: linear-gradient(135deg, #0e7490 0%, #0f766e 100%);
    color: #ffffff !important;
    filter: brightness(1.03);
    box-shadow: 0 10px 22px rgba(14, 116, 144, .24);
    transform: translateY(-1px);
}

.stButton > button:active, .stDownloadButton > button:active {
    transform: translateY(0);
}

.stButton > button:focus, .stDownloadButton > button:focus {
    color: #ffffff !important;
    border-color: #155e75;
    box-shadow: 0 0 0 3px rgba(20, 184, 166, .28);
}

.stButton > button p, .stDownloadButton > button p,
.stButton > button span, .stDownloadButton > button span {
    color: #ffffff !important;
    font-weight: 800 !important;
}

div[data-testid="stExpander"] {
    border: 1px solid #cfe4ee;
    border-radius: 8px;
    background: #ffffff;
}

@media (max-width: 768px) {
    .block-container {
        padding: .85rem .75rem 2rem;
    }

    .compact-card, .card, .metric-card {
        padding: .85rem;
    }

    .topbar-row {
        align-items: flex-start;
        flex-direction: column;
    }

    .chip-row {
        justify-content: flex-start;
    }
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOAD MODEL (CACHED)
# ============================================================
@st.cache_resource
def load_model():

    with st.spinner("⬇️ Loading AI model from Hugging Face..."):

        model_path = hf_hub_download(
            repo_id="reddysorgs/skin-cancer-cdss-model",
            filename="final_resnet_texture_model.pth"
        )

        model = ResNetTextureFusion()
        model.load_state_dict(
            torch.load(model_path, map_location="cpu")
        )
        model.eval()

    return model




model =None

gradcam = None


# ============================================================
# SIDEBAR BRANDING / NAVIGATION
# ============================================================
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-title">Skin Lesion CDSS</div>
        <div class="sidebar-brand-subtitle">AI screening support workspace</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Workflow**")
    st.markdown("1. Upload image")
    st.markdown("2. Validate lesion focus")
    st.markdown("3. Run prediction")
    st.markdown("4. Review heatmap")
    st.markdown("5. Download report")

    st.divider()
    st.markdown("**Model Information**")
    st.markdown("Architecture: ResNet18 + Texture Fusion")
    st.markdown("Input Size: 224 x 224")
    st.markdown("Texture Features: GLCM + Wavelet")
    st.markdown("Classes: Benign / Malignant")
    st.markdown("Explainability: Grad-CAM")
    st.markdown("Report: PDF Clinical Summary")

    st.divider()
    st.caption("Educational decision-support tool. Not a final diagnosis.")


# ============================================================
# HEADER + INTAKE
# ============================================================
st.markdown("""
<div class="app-topbar">
    <div class="topbar-row">
        <div>
            <div class="eyebrow">Clinical AI Screening Workspace</div>
            <h1>Skin Lesion Decision Support</h1>
            <p class="topbar-copy">
                Upload one focused lesion or wound image to run validation, AI inference,
                ABCDE analysis, visual explanation, and report generation.
            </p>
        </div>
        <div class="chip-row">
            <span class="chip">Image Gate</span>
            <span class="chip">ResNet + Texture</span>
            <span class="chip">Grad-CAM</span>
            <span class="chip">PDF Report</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

upload_panel, readiness_panel = st.columns([1.15, .85], gap="large")

with upload_panel:
    with st.container(border=True):
        st.markdown("""
        <div class="section-title">Case Intake</div>
        <p class="muted">Use a close-up dermoscopic or wound/lesion crop. Avoid portraits, full-body photos, and unrelated objects.</p>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload lesion image",
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed"
        )

with readiness_panel:
    st.markdown("""
    <div class="tool-card">
        <div class="section-title">Analysis Workflow</div>
        <div class="step-list">
            <div class="step-item"><span class="step-dot">1</span><span>Validate image type and lesion focus</span></div>
            <div class="step-item"><span class="step-dot">2</span><span>Run hybrid AI prediction</span></div>
            <div class="step-item"><span class="step-dot">3</span><span>Compute ABCDE clinical indicators</span></div>
            <div class="step-item"><span class="step-dot">4</span><span>Generate heatmap and report</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# MAIN PIPELINE
# ============================================================
if uploaded_file is not None:

    if model is None:
        model = load_model()
        gradcam = GradCAM(model, model.backbone.layer4[-1])


    # ---------------- IMAGE ----------------
    image = Image.open(uploaded_file).convert("RGB")
    original_col, heatmap_col = st.columns(2, gap="large")

    with original_col:
        st.markdown('<div class="section-title">Uploaded Image</div>', unsafe_allow_html=True)
        st.image(image, caption="Original input", use_container_width=True)

    is_valid_skin_image, validation_reasons, validation_metrics = validate_skin_lesion_image(image)

    if not is_valid_skin_image:
        st.error("This does not look like a valid skin lesion image.")
        st.markdown(
            """
            Please upload a clear dermoscopic or close-up skin lesion image.
            The AI model is trained for skin lesion screening only, so unrelated
            images should not be classified as Benign or Malignant.
            """
        )
        with st.expander("Why was this image rejected?"):
            for reason in validation_reasons:
                st.write(f"- {reason}")
            st.write(
                {
                    "skin_region_ratio": round(validation_metrics["skin_ratio"], 3),
                    "lesion_candidate_ratio": round(validation_metrics["largest_contour_ratio"], 3),
                    "abnormal_region_ratio": round(validation_metrics["abnormal_region_ratio"], 3),
                    "face_detected": validation_metrics["face_detected"],
                    "image_contrast": round(validation_metrics["contrast"], 2),
                }
            )
        st.stop()

    quality_contrast = validation_metrics["contrast"]
    quality_skin_ratio = validation_metrics["skin_ratio"] * 100
    quality_focus_ratio = validation_metrics["abnormal_region_ratio"] * 100
    quality_face_status = "Passed" if not validation_metrics["face_detected"] else "Review"
    quality_contrast_label = "Good" if quality_contrast >= 28 else "Fair"
    current_upload_name = getattr(uploaded_file, "name", "uploaded_image")
    if st.session_state.get("case_upload_name") != current_upload_name:
        st.session_state.case_upload_name = current_upload_name
        st.session_state.case_id = f"SKIN-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    case_id = st.session_state.case_id

    pipeline_status = st.status("Processing clinical analysis...", expanded=True)
    pipeline_progress = st.progress(0)
    pipeline_status.write("Preprocessing Image")
    pipeline_progress.progress(15)

    # ========================================================
    # ABCDE FEATURE EXTRACTION (LOGIC UNCHANGED)
    # ========================================================
    asymmetry_score = compute_asymmetry(image)
    border_score = compute_border_irregularity(image)
    color_count = compute_color_variation(image)
    diameter_mm = compute_diameter(image)
    evolution_score, evolution_label = compute_evolution_score(
        asymmetry_score, border_score, color_count
    )

    # ---------------- LABELS ----------------
    asym_label = (
        "Low" if asymmetry_score < 0.20 else
        "Moderate" if asymmetry_score < 0.50 else
        "High" if asymmetry_score < 0.75 else
        "Severe"
    )

    border_label = (
        "Regular" if border_score < 1.5 else
        "Mild Irregularity" if border_score < 2.0 else
        "Irregular" if border_score < 2.5 else
        "Highly Irregular"
    )

    color_label = (
        "Low" if color_count <= 2 else
        "Moderate" if color_count == 3 else
        "High"
    )

    diameter_label = (
        "Below Risk Threshold" if diameter_mm < 6
        else "Above Risk Threshold"
    )

    # ========================================================
    # MODEL PREDICTION (LOGIC UNCHANGED)
    # ========================================================


    image_tensor = preprocess_image(image)
    pipeline_status.write("Extracting Features")
    pipeline_progress.progress(35)

    texture_tensor = extract_texture_features(image)

    if model is None:
        st.info("🔬 Model inference is disabled in cloud demo.")
        st.stop()

    pipeline_status.write("Running CNN Analysis")
    pipeline_progress.progress(55)

    with torch.no_grad():
        outputs = model(image_tensor, texture_tensor)
        probs = torch.softmax(outputs, dim=1)
        confidence, pred = torch.max(probs, dim=1)

    label_map = {0: "Benign", 1: "Malignant"}
    predicted_label = label_map[pred.item()]
    confidence_score = confidence.item() * 100
    benign_probability = probs[0, 0].item() * 100
    malignant_probability = probs[0, 1].item() * 100

    if malignant_probability >= 70:
        model_risk_label, model_risk_class = "HIGH RISK", "high"
    elif malignant_probability >= 35:
        model_risk_label, model_risk_class = "MODERATE RISK", "mid"
    else:
        model_risk_label, model_risk_class = "LOW RISK", "low"

    # ========================================================
    # GRAD-CAM (EXPLAINABILITY)
    # ========================================================
    if gradcam is not None:
        pipeline_status.write("Generating Grad-CAM")
        pipeline_progress.progress(75)

        cam = gradcam.generate(image_tensor, texture_tensor)
        heatmap_overlay = overlay_heatmap_on_image(image, cam)
        heatmap_pil = Image.fromarray(heatmap_overlay)

        with heatmap_col:
            st.markdown('<div class="section-title">Attention Heatmap</div>', unsafe_allow_html=True)
            st.image(
                heatmap_pil,
                caption="Regions influencing the AI decision",
                use_container_width=True
            )
    else:
        heatmap_pil = image
        with heatmap_col:
            st.info("Explainable AI unavailable in this environment.")

    pipeline_status.write("Creating Clinical Summary")
    pipeline_progress.progress(90)



    # ========================================================
    # RISK ASSESSMENT (LOGIC UNCHANGED)
    # ========================================================
    risk_score = 0
    reasons = []

    if asym_label in ["High", "Severe"]:
        risk_score += 1
        reasons.append("High asymmetry detected")

    if border_label in ["Irregular", "Highly Irregular"]:
        risk_score += 1
        reasons.append("Irregular lesion border")

    if color_label in ["Moderate", "High"]:
        risk_score += 1
        reasons.append("Multiple color variation")

    if diameter_mm >= 6:
        risk_score += 1
        reasons.append("Diameter above 6 mm")

    if evolution_label in ["Moderate Change", "Rapid Change"]:
        risk_score += 1
        reasons.append("Noticeable lesion evolution")

    if predicted_label == "Malignant" and confidence_score >= 70:
        risk_score += 2
        reasons.append("High model confidence for malignancy")

    if risk_score >= 4:
        risk_level, risk_class = "HIGH", "high"
    elif risk_score >= 2:
        risk_level, risk_class = "MODERATE", "mid"
    else:
        risk_level, risk_class = "LOW", "low"

    pipeline_status.update(label="Clinical analysis completed", state="complete", expanded=False)
    pipeline_progress.progress(100)

    # ========================================================
    # STRUCTURED ABCDE DATA (FOR AI & PDF)
    # ========================================================
    abcd_results = {
        "A – Asymmetry": f"{asym_label} ({asymmetry_score:.2f})",
        "B – Border": f"{border_label} ({border_score:.2f})",
        "C – Color": f"{color_label} ({color_count} colors)",
        "D – Diameter": f"{diameter_mm:.2f} mm ({diameter_label})",
        "E – Evolution": evolution_label
    }

    # ========================================================
    # DISPLAY RESULTS
    # ========================================================
    st.markdown('<div class="section-title">Analysis Results</div>', unsafe_allow_html=True)
    pred_col, conf_col, risk_col = st.columns(3, gap="medium")

    with pred_col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Prediction</div>
            <div class="metric-value">{predicted_label}</div>
        </div>
        """, unsafe_allow_html=True)

    with conf_col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Confidence</div>
            <div class="metric-value">{confidence_score:.2f}%</div>
        </div>
        """, unsafe_allow_html=True)

    with risk_col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Risk Level</div>
            <div class="metric-value"><span class="badge {risk_class}">{risk_level}</span></div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="compact-card">
        <div class="section-title">Case Reference</div>
        <p class="muted"><b>Case ID:</b> {case_id}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="probability-grid">
        <div class="probability-card">
            <div class="probability-label">Benign Probability</div>
            <div class="probability-value">{benign_probability:.2f}%</div>
        </div>
        <div class="probability-card">
            <div class="probability-label">Malignant Probability</div>
            <div class="probability-value">{malignant_probability:.2f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="compact-card">
        <div class="section-title">Image Quality Check</div>
        <div class="quality-grid">
            <div class="quality-card">
                <div class="quality-label">Contrast</div>
                <div class="quality-value">{quality_contrast_label}</div>
            </div>
            <div class="quality-card">
                <div class="quality-label">Skin Region</div>
                <div class="quality-value">{quality_skin_ratio:.1f}%</div>
            </div>
            <div class="quality-card">
                <div class="quality-label">Lesion Focus</div>
                <div class="quality-value">{quality_focus_ratio:.2f}%</div>
            </div>
            <div class="quality-card">
                <div class="quality-label">Face Check</div>
                <div class="quality-value">{quality_face_status}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="risk-meter-card">
        <div class="risk-meter-row">
            <div>
                <div class="risk-meter-title">Model Risk Meter</div>
                <p class="muted">Estimated malignant probability from the current model output.</p>
            </div>
            <div>
                <span class="badge {model_risk_class}">{model_risk_label}</span>
            </div>
        </div>
        <div class="risk-meter-value">Malignant probability: {malignant_probability:.2f}%</div>
    </div>
    """, unsafe_allow_html=True)
    st.progress(int(round(malignant_probability)))

    abcd_col, risk_reason_col = st.columns([1.15, 1], gap="large")

    with abcd_col:
        st.markdown(f"""
        <div class="compact-card">
            <div class="section-title">ABCDE Clinical Analysis</div>
            {''.join([f"<p><b>{k}:</b> {v}</p>" for k,v in abcd_results.items()])}
        </div>
        """, unsafe_allow_html=True)

    with risk_reason_col:
        risk_items = ''.join(f"<li>{r}</li>" for r in reasons) or "<li>No high-risk rule triggered.</li>"
        st.markdown(f"""
        <div class="compact-card">
            <div class="section-title">Risk Reasoning</div>
            <span class="badge {risk_class}">Risk Level: {risk_level}</span>
            <ul class="result-list">{risk_items}</ul>
        </div>
        """, unsafe_allow_html=True)

    # ========================================================
    # AI CLINICAL SUMMARY (EXPANDABLE)
    # ========================================================
    ai_summary_payload = f"""
    Prediction: {predicted_label} ({confidence_score:.2f}%)
    Risk Level: {risk_level}
    ABCDE: {abcd_results}
    """

    with st.expander("🤖 Analyze with AI (Clinical Summary)"):
        if st.button("Run AI Analysis"):
            with st.spinner("Running AI clinical analysis..."):
                st.session_state.ai_response = generate_ai_summary(ai_summary_payload)

        if st.session_state.ai_response:
            st.markdown(st.session_state.ai_response)

        # ========================================================
    # PATIENT GUIDANCE (NEW – SAFE ADDITION)
    # ========================================================
    from ai_engine import generate_patient_guidance

    with st.expander("💚 Personalized Patient Guidance", expanded=False):

        st.markdown(
            """
            This section provides **patient-friendly guidance** based on
            your AI analysis. It is designed to help you understand
            precautions, daily care, and when to seek medical advice.
            """
        )

        if st.button("Generate Patient Guidance"):
            with st.spinner("Preparing personalized guidance..."):
                st.session_state.patient_guidance = generate_patient_guidance(
                predicted_label=predicted_label,
                risk_level=risk_level,
                abcd_results=abcd_results
                )


        if st.session_state.patient_guidance:
            st.markdown(st.session_state.patient_guidance)


            st.markdown(
                """
                <p style="font-size:13px; color:#64748b;">
                ⚠️ This guidance is for educational support only.
                Always consult a certified dermatologist for diagnosis
                and treatment decisions.
                </p>
                """,
                unsafe_allow_html=True
            )



    # ========================================================
    # PDF REPORT GENERATION
    # ========================================================
    safe_case_id = case_id.replace("-", "_")
    st.markdown("""
    <div class="report-panel">
        <div class="report-title">Download Clinical Report</div>
        <p class="muted">Generate a structured PDF with the image, heatmap, prediction, ABCDE values, and AI guidance.</p>
        <div class="report-checklist">
            <div class="report-check-item">Original Image</div>
            <div class="report-check-item">Grad-CAM Heatmap</div>
            <div class="report-check-item">Prediction Result</div>
            <div class="report-check-item">Risk Level</div>
            <div class="report-check-item">ABCDE Analysis</div>
            <div class="report-check-item">Clinical Guidance</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    os.makedirs("temp_reports", exist_ok=True)
    uid = safe_case_id
    pdf_path = f"temp_reports/report_{uid}.pdf"
    orig_path = f"temp_reports/original_{uid}.png"
    heatmap_path = f"temp_reports/heatmap_{uid}.png"

    image.save(orig_path)

# 🔧 FIX: save PIL heatmap, not NumPy array
    heatmap_pil.save(heatmap_path)


    if st.button("Generate PDF Report"):
        generate_pdf_report(
            file_path=pdf_path,
            original_image_path=orig_path,
            heatmap_image_path=heatmap_path,
            prediction=predicted_label,
            confidence=confidence_score,
            risk_level=risk_level,
            abcd_results=abcd_results,
            ai_summary=(
                (st.session_state.get("ai_response") or "AI clinical summary not generated.")
                + "\n\n---\n\n"
                + (st.session_state.get("patient_guidance") or "Patient guidance not generated.")
            ),
            case_id=case_id
        )



        with open(pdf_path, "rb") as f:
            st.download_button(
                "⬇ Download PDF Report",
                data=f,
                file_name=f"Skin_Cancer_Report_{safe_case_id}.pdf",
                mime="application/pdf"
            )

else:
    st.markdown("""
    <div class="compact-card">
        <div class="section-title">Ready for Analysis</div>
        <p class="muted">
            Upload a valid lesion or wound image above. Results, heatmap, ABCDE scoring,
            AI summary, and report controls will appear here after the image passes validation.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<p style="text-align:center; font-size:14px; color:#64748b; margin-top:40px;">
Developed by Manikanta | Final Year Project | AI & Data Science
</p>
""", unsafe_allow_html=True)

