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


def _safe_image(path, width, height):
    if path and os.path.exists(path):
        return RLImage(path, width=width, height=height)
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
    case_id=None
):
    """Generate a structured clinical decision-support PDF report."""

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
        ["Patient ID", "Anonymous"],
        ["Model Output", str(prediction)],
        ["Confidence", f"{confidence:.2f}%"],
        ["Overall Risk Level", str(risk_level)],
    ]
    story.append(_table(meta_rows, [4.5 * cm, 10.5 * cm], styles))

    _section(story, "Image Review", styles)
    image_table = Table(
        [
            [
                Paragraph("Uploaded Image", styles["CellBold"]),
                Paragraph("Grad-CAM Attention Heatmap", styles["CellBold"]),
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

    _section(story, "ABCDE Clinical Indicators", styles)
    abcd_rows = [["Indicator", "Result"]]
    abcd_rows.extend([[key, value] for key, value in abcd_results.items()])
    story.append(_table(abcd_rows, [5.4 * cm, 9.6 * cm], styles, header=True))

    _section(story, "AI Clinical Interpretation", styles)
    for line in _clean_ai_text(ai_summary):
        story.append(Paragraph(f"&#8226; {html.escape(line)}", styles["Body"]))

    _section(story, "Clinical Safety Note", styles)
    warning_table = Table(
        [[Paragraph(
            "This report is generated by an AI-based clinical decision support prototype. "
            "It must not be used as a final diagnosis. A certified dermatologist should "
            "confirm all concerning findings through clinical examination and appropriate tests.",
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
