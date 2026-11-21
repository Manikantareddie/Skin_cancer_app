from datetime import datetime
import html
import os
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PRIMARY = colors.HexColor("#0F766E")
NAVY = colors.HexColor("#16324F")
TEXT = colors.HexColor("#334155")
MUTED = colors.HexColor("#64748B")
LINE = colors.HexColor("#D7E4ED")
SOFT = colors.HexColor("#F0FDFA")
WARNING = colors.HexColor("#FEF3C7")


def _build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=NAVY,
        alignment=TA_CENTER,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Subtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="Section",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=NAVY,
        spaceBefore=8,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Body",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=TEXT,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="Small",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=MUTED,
    ))
    styles.add(ParagraphStyle(
        name="Cell",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=TEXT,
    ))
    styles.add(ParagraphStyle(
        name="CellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=NAVY,
    ))
    return styles


def _clean_ai_text(text):
    if not text:
        return ["AI clinical summary was not generated."]

    cleaned_lines = []
    for raw_line in str(text).splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if set(line) <= {"-", "_", "*"}:
            continue

        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"^[-*]\s+", "", line)
        line = re.sub(r"^\d+[\.)]\s+", "", line)
        line = line.replace("**", "")
        line = line.replace("__", "")
        line = line.replace("`", "")
        line = re.sub(r"\[(.*?)\]\((.*?)\)", r"\1", line)
        line = re.sub(r"\s{2,}", " ", line).strip()

        if line:
            cleaned_lines.append(line)

    return cleaned_lines or ["AI clinical summary was not generated."]


def _p(text, style):
    return Paragraph(html.escape(str(text)), style)


def _section(story, title, styles):
    story.append(Spacer(1, 8))
    story.append(Paragraph(html.escape(title), styles["Section"]))


def _table(rows, col_widths, styles, header=False):
    data = []
    for row_index, row in enumerate(rows):
        style = styles["CellBold"] if header and row_index == 0 else styles["Cell"]
        data.append([Paragraph(html.escape(str(cell)), style) for cell in row])

    table = Table(data, colWidths=col_widths, hAlign="LEFT")
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), SOFT),
            ("TEXTCOLOR", (0, 0), (-1, 0), NAVY),
        ])
    table.setStyle(TableStyle(commands))
    return table


def _safe_image(path_or_buf, width, height):
    if hasattr(path_or_buf, "read"):
        try:
            return RLImage(path_or_buf, width=width, height=height)
        except Exception:
            return Paragraph("Image unavailable", _build_styles()["Small"])
    if path_or_buf and isinstance(path_or_buf, str) and os.path.exists(path_or_buf):
        return RLImage(path_or_buf, width=width, height=height)
    return Paragraph("Image unavailable", _build_styles()["Small"])


def generate_pdf_report(
    file_path,
    original_image_path,
    heatmap_image_path,
    prediction,
    confidence,
    risk_level,
    abcd_results,
    ai_summary,
    case_id=None,
    difference_image_path=None,
    diameter_detail=None,
    evolution_detail=None,
):
    """Generate a structured clinical decision-support PDF report with D and E evaluation."""

    styles = _build_styles()
    story = []
    date_str = datetime.now().strftime("%d %b %Y, %I:%M %p")

    story.append(Paragraph("AI Skin Lesion Screening Report", styles["ReportTitle"]))
    story.append(Paragraph(
        "Clinical Decision Support System | Educational screening output, not a medical diagnosis",
        styles["Subtitle"],
    ))

    meta_rows = [
        ["Report Date", date_str],
        ["Case ID", case_id or "Not assigned"],
        ["Patient Reference", "Anonymous Patient Screening"],
        ["Screening Classification", f"Model classified into '{prediction}' category"],
        ["Model Output Score", f"{confidence:.2f}% (Uncalibrated neural network output score)"],
        ["Benchmark Context", "ResNet18 + Texture Fusion (84.23% test accuracy, 80.89% recall)"],
        ["Overall Risk Category", str(risk_level)],
    ]
    story.append(_table(meta_rows, [4.5 * cm, 10.5 * cm], styles))

    _section(story, "Image Review & Neural Attention", styles)
    image_table = Table(
        [
            [
                Paragraph("Uploaded Lesion Photo", styles["CellBold"]),
                Paragraph("Grad-CAM Neural Attention Heatmap", styles["CellBold"]),
            ],
            [
                _safe_image(original_image_path, 7.1 * cm, 6.2 * cm),
                _safe_image(heatmap_image_path, 7.1 * cm, 6.2 * cm),
            ],
        ],
        colWidths=[7.45 * cm, 7.45 * cm],
        hAlign="LEFT",
    )
    image_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("BACKGROUND", (0, 0), (-1, 0), SOFT),
        ("ALIGN", (0, 1), (-1, 1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(image_table)

    # Optional Longitudinal Difference Section if available
    if difference_image_path:
        _section(story, "Longitudinal Image Registration & Difference Overlay", styles)
        diff_table = Table(
            [
                [Paragraph("Registered Difference Overlay (Green=Stable, Red=Expanded, Blue=Baseline)", styles["CellBold"])],
                [_safe_image(difference_image_path, 14.5 * cm, 6.5 * cm)],
            ],
            colWidths=[14.9 * cm],
            hAlign="LEFT",
        )
        diff_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.35, LINE),
            ("BACKGROUND", (0, 0), (-1, 0), SOFT),
            ("ALIGN", (0, 1), (-1, 1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(diff_table)

    _section(story, "ABCDE Clinical Indicators", styles)
    abcd_rows = [["Indicator", "Evaluated Finding"]]
    abcd_rows.extend([[key, value] for key, value in abcd_results.items()])
    story.append(_table(abcd_rows, [5.4 * cm, 9.6 * cm], styles, header=True))

    if diameter_detail or evolution_detail:
        detail_rows = []
        if diameter_detail:
            detail_rows.append(["Diameter Provenance & Context", str(diameter_detail)])
        if evolution_detail:
            detail_rows.append(["Evolution Provenance & History", str(evolution_detail)])
        story.append(Spacer(1, 4))
        story.append(_table(detail_rows, [5.4 * cm, 9.6 * cm], styles))

    _section(story, "AI Clinical Interpretation", styles)
    for line in _clean_ai_text(ai_summary):
        story.append(Paragraph(f"&#8226; {html.escape(line)}", styles["Body"]))

    _section(story, "Clinical Safety Note & Limitations", styles)
    warning_table = Table(
        [[Paragraph(
            "This educational screening report is generated by an automated clinical decision support prototype. "
            "It must not be interpreted as a medical diagnosis or treatment plan. "
            "Important clinical principles: (1) 6 mm is a clinical reference guideline, not an absolute diagnostic boundary. "
            "(2) Photographic differences (lighting, camera distance, angle) can simulate physical variation and do not confirm biological progression. "
            "(3) Machine learning classifiers can produce false positives and false negatives. "
            "A board-certified dermatologist should conduct an in-person physical dermoscopy examination and pathology biopsy if clinically indicated.",
            styles["Body"],
        )]],
        colWidths=[15 * cm],
    )
    warning_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), WARNING),
        ("BOX", (0, 0), (-1, -1), 0.35, colors.HexColor("#F59E0B")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(warning_table)

    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Generated by AI Skin Cancer Detection and CDSS.",
        styles["Small"],
    ))

    pdf = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        rightMargin=1.7 * cm,
        leftMargin=1.7 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
        title="AI Skin Lesion Screening Report",
        author="AI Skin Cancer Detection CDSS",
    )
    pdf.build(story)
