from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from datetime import datetime
import os


def generate_pdf_report(
    file_path,
    original_image_path,
    heatmap_image_path,
    prediction,
    confidence,
    risk_level,
    abcd_results,
    ai_summary
):
    """
    Generates a clinical PDF report.
    """

    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(
        "<b>AI Skin Cancer Detection Report</b>",
        styles["Title"]
    ))
    story.append(Spacer(1, 12))

    # Meta info
    date_str = datetime.now().strftime("%d %b %Y, %I:%M %p")
    story.append(Paragraph(f"<b>Date:</b> {date_str}", styles["Normal"]))
    story.append(Paragraph("<b>Patient ID:</b> Anonymous", styles["Normal"]))
    story.append(Spacer(1, 12))

    # Images
    story.append(Paragraph("<b>Uploaded Skin Image</b>", styles["Heading3"]))
    story.append(RLImage(original_image_path, width=8*cm, height=8*cm))
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>Grad-CAM Heatmap</b>", styles["Heading3"]))
    story.append(RLImage(heatmap_image_path, width=8*cm, height=8*cm))
    story.append(Spacer(1, 12))

    # Prediction
    story.append(Paragraph("<b>Model Prediction</b>", styles["Heading3"]))
    story.append(Paragraph(
        f"Detected Class: <b>{prediction}</b><br/>"
        f"Confidence Score: <b>{confidence:.2f}%</b><br/>"
        f"Risk Level: <b>{risk_level}</b>",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    # ABCDE
    story.append(Paragraph("<b>ABCDE Analysis</b>", styles["Heading3"]))
    for key, value in abcd_results.items():
        story.append(Paragraph(f"{key}: {value}", styles["Normal"]))
    story.append(Spacer(1, 12))

   
        # ==============================
    # AI CLINICAL INTERPRETATION
    # ==============================
    story.append(Paragraph("<b>AI Clinical Interpretation</b>", styles["Heading3"]))
    story.append(Spacer(1, 6))

    summary_lines = ai_summary.split("\n")

    for line in summary_lines:
        if line.strip():
            story.append(Paragraph(f"• {line.strip()}", styles["Normal"]))

    story.append(Spacer(1, 12))


    # Disclaimer
    story.append(Paragraph(
        "<i>Disclaimer: This system is a clinical decision support tool. "
        "Final diagnosis must be confirmed by a certified dermatologist.</i>",
        styles["Italic"]
    ))

    # Build PDF
    pdf = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    pdf.build(story)
