# ============================================================
# AI SKIN CANCER DETECTION SYSTEM
# Final Year Project | AI & Data Science
# ============================================================
import streamlit as st
import torch
import os
import uuid


from huggingface_hub import hf_hub_download

from PIL import Image



# ---------------- AI & MODEL IMPORTS ----------------
from model import CNNWithTexture
from utils import (
    preprocess_image,
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
    page_icon="🧬",
    layout="centered"
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

/* App Background */
.stApp {
    background-color: #eef4f8;
    color: #425b76;
}

/* Container */
.block-container {
    max-width: 1100px;
    padding-top: 2.2rem;
}

/* Cards */
.card {
    background-color: #f6fbff;
    border-radius: 18px;
    padding: 24px;
    border: 1px solid #dbe7f1;
    margin-top: 24px;
}

/* Headings */
h1 {
    color: #0f2a44;
    font-weight: 700;
}
h2, h3 {
    color: #1f4e79;
}

/* Text */
p, li {
    color: #425b76;
    font-size: 15px;
}

/* Accent icons */
.icon {
    color: #3aa6b9;
}

/* Risk badges */
.badge {
    padding: 6px 18px;
    border-radius: 999px;
    font-weight: 600;
    font-size: 14px;
}

.low {
    background-color: #e6f7f0;
    color: #1b7f5f;
}

.mid {
    background-color: #fff6e1;
    color: #9a6b00;
}

.high {
    background-color: #fdecea;
    color: #b3261e;
}

/* Buttons */
.stButton > button {
    background-color: #white;
    color: #ffffff;
    border-radius: 10px;
    border: none;
    padding: 10px 20px;
    font-weight: 600;
}

.stButton > button:hover {
    background-color: white;
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
            filename="final_cnn_texture_model.pth"
        )

        model = CNNWithTexture()
        model.load_state_dict(
            torch.load(model_path, map_location="cpu")
        )
        model.eval()

    return model




model =None

gradcam = None



# ============================================================
# HEADER
# ============================================================
st.markdown("""
<h1 style="text-align:center;">🧬 AI Skin Cancer Detection System</h1>
<p style="text-align:center; color:#475569;">
Final Year Project – Explainable AI for Medical Imaging
</p>
""", unsafe_allow_html=True)

# ============================================================
# PROJECT OVERVIEW
# ============================================================
st.markdown("""
<div class="card">
<h3>📌 Project Overview</h3>
<p>
This system combines <b>deep learning</b>, <b>ABCDE clinical rules</b>,
and <b>explainable AI (Grad-CAM)</b> to assist in early skin cancer
risk assessment.
</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# IMAGE UPLOAD
# ============================================================
st.markdown("""
<div class="card">
<h3>📤 Upload Dermoscopic Image</h3>
<p>Supported formats: JPG, PNG</p>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Upload Image",
    type=["jpg", "jpeg", "png"],
    label_visibility="collapsed"
)

# ============================================================
# MAIN PIPELINE
# ============================================================
if uploaded_file is not None:

    if model is None:
        model = load_model()
        gradcam = GradCAM(model, model.cnn[-3])


    # ---------------- IMAGE ----------------
    image = Image.open(uploaded_file).convert("RGB")
    st.image(image, width=520)

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
    texture_tensor = extract_texture_features(image)

    if model is None:
        st.info("🔬 Model inference is disabled in cloud demo.")
        st.stop()

    with torch.no_grad():
        outputs = model(image_tensor, texture_tensor)
        probs = torch.softmax(outputs, dim=1)
        confidence, pred = torch.max(probs, dim=1)

    label_map = {0: "Benign", 1: "Malignant"}
    predicted_label = label_map[pred.item()]
    confidence_score = confidence.item() * 100



    


    # ========================================================
    # GRAD-CAM (EXPLAINABILITY)
    # ========================================================
    if gradcam is not None:
        cam = gradcam.generate(image_tensor, texture_tensor)
        heatmap_overlay = overlay_heatmap_on_image(image, cam)
        heatmap_pil = Image.fromarray(heatmap_overlay)

        st.markdown("### 🔥 Explainable AI – Attention Heatmap")
        st.image(
            heatmap_pil,
            caption="Regions influencing the AI decision",
            width=420
        )
    else:
     st.info("🧠 Explainable AI unavailable in cloud demo.")



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
    st.markdown(f"""
    <div class="card">
    <h3>🔍 Model Prediction</h3>
    <p><b>Detected Class:</b> {predicted_label}</p>
    <p><b>Confidence:</b> {confidence_score:.2f}%</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
    <h3>🧪 ABCDE Clinical Analysis</h3>
    {''.join([f"<p><b>{k}:</b> {v}</p>" for k,v in abcd_results.items()])}
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="card">
    <h3>🩺 Overall Risk Assessment</h3>
    <span class="badge {risk_class}">Risk Level: {risk_level}</span>
    <ul>{''.join(f"<li>{r}</li>" for r in reasons)}</ul>
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
            st.session_state.ai_response = generate_ai_summary(ai_summary_payload)
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
    st.markdown("### 📄 Download Clinical Report")

    os.makedirs("temp_reports", exist_ok=True)
    uid = str(uuid.uuid4())[:8]
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
            )
        )



        with open(pdf_path, "rb") as f:
            st.download_button(
                "⬇ Download PDF Report",
                data=f,
                file_name=f"Skin_Cancer_Report_{uid}.pdf",
                mime="application/pdf"
            )

else:
    st.info("Upload an image to start analysis.")

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<p style="text-align:center; font-size:14px; color:#64748b; margin-top:40px;">
Developed by Manikanta | Final Year Project | AI & Data Science
</p>
""", unsafe_allow_html=True)
