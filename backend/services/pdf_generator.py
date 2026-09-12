"""
pdf_generator.py -- Generates a downloadable medical-style AI Screening Summary Report using ReportLab.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_patient_pdf(data: dict) -> io.BytesIO:
    """
    Generates a professional clinical-style screening summary PDF.
    Expects data dictionary with:
      patient: {name, age, sex}
      report_info: {filename, date}
      parameters: {haemoglobin, platelet_count, pdw, wbc_count}
      prediction: {risk_level, probability, message}
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.HexColor("#0f172a"),
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#64748b"),
        alignment=TA_LEFT,
        spaceAfter=12,
    )
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#78350f"),
    )

    elements = []

    # 1. Header Banner
    header_table = Table(
        [
            [
                Paragraph("<b>Nexus AI</b> Clinical Screening Summary", title_style),
                Paragraph(
                    f"Report Date: <b>{datetime.now().strftime('%d %b %Y, %H:%M')}</b><br/>"
                    f"Status: <b>Completed</b>",
                    ParagraphStyle("RightH", parent=styles["Normal"], fontSize=8, alignment=TA_RIGHT, textColor=colors.HexColor("#475569")),
                ),
            ]
        ],
        colWidths=[380, 160],
    )
    header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    elements.append(header_table)
    elements.append(Paragraph("Nexus AI — Dengue Risk Screening & Clinical Decision Support", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#e2e8f0"), spaceAfter=10))

    # 2. Prominent Non-Diagnostic Alert Box
    disclaimer_table = Table(
        [
            [
                Paragraph(
                    "<b>IMPORTANT NOTICE:</b> This document is an <b>AI-assisted screening estimate</b> generated for "
                    "educational and research support. It is <b>NOT</b> an official laboratory diagnosis or certified physician report. "
                    "Clinical evaluation, confirmatory antigen/antibody tests (e.g. NS1, IgM/IgG), and medical oversight are required.",
                    disclaimer_style,
                )
            ]
        ],
        colWidths=[540],
    )
    disclaimer_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef3c7")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#f59e0b")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    elements.append(disclaimer_table)
    elements.append(Spacer(1, 10))

    # 3. Patient & Document Information Table
    elements.append(Paragraph("Patient & Document Information", section_style))
    patient_info = data.get("patient", {})
    report_info = data.get("report_info", {})

    patient_rows = [
        [
            Paragraph("<b>Patient Name:</b>", body_style),
            Paragraph(str(patient_info.get("name") or "Not Specified"), body_style),
            Paragraph("<b>Biological Sex:</b>", body_style),
            Paragraph(str(patient_info.get("sex", "")).capitalize() or "N/A", body_style),
        ],
        [
            Paragraph("<b>Patient Age:</b>", body_style),
            Paragraph(f"{patient_info.get('age', 'N/A')} years", body_style),
            Paragraph("<b>Source File:</b>", body_style),
            Paragraph(str(report_info.get("filename") or "Direct Entry"), body_style),
        ],
    ]
    patient_table = Table(patient_rows, colWidths=[95, 175, 95, 175])
    patient_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(patient_table)
    elements.append(Spacer(1, 12))

    # 4. Blood Test Parameters Table
    elements.append(Paragraph("Laboratory Parameters Evaluated", section_style))
    params = data.get("parameters", {})
    plt = float(params.get("platelet_count") or 0)
    hb = float(params.get("haemoglobin") or 0)
    pdw = float(params.get("pdw") or 0)
    wbc = float(params.get("wbc_count") or 0)

    def plt_status(val):
        if val < 50000:
            return "Severe Thrombocytopenia (<50k)", colors.HexColor("#dc2626")
        elif val < 100000:
            return "Critical Low (<100k)", colors.HexColor("#ea580c")
        elif val < 150000:
            return "Borderline Low", colors.HexColor("#d97706")
        elif val <= 450000:
            return "Normal Range", colors.HexColor("#16a34a")
        return "Elevated", colors.HexColor("#2563eb")

    def hb_status(val):
        if val < 11.5:
            return "Low (Anaemia risk)", colors.HexColor("#d97706")
        elif val <= 17.5:
            return "Normal Range", colors.HexColor("#16a34a")
        return "High / Haemoconcentration", colors.HexColor("#ea580c")

    def pdw_status(val):
        if val > 17.0:
            return "Elevated (Platelet Anisocytosis)", colors.HexColor("#ea580c")
        elif val < 9.0:
            return "Low", colors.HexColor("#64748b")
        return "Normal Range", colors.HexColor("#16a34a")

    plt_stat, plt_color = plt_status(plt)
    hb_stat, hb_color = hb_status(hb)
    pdw_stat, pdw_color = pdw_status(pdw)

    lab_headers = [
        Paragraph("<b>Test Parameter</b>", body_style),
        Paragraph("<b>Patient Value</b>", body_style),
        Paragraph("<b>Reference Range</b>", body_style),
        Paragraph("<b>Clinical Interpretation</b>", body_style),
    ]

    lab_rows = [
        lab_headers,
        [
            Paragraph("<b>Platelet Count</b>", body_style),
            Paragraph(f"<b>{int(plt):,}</b> cells/µL", body_style),
            Paragraph("150,000 – 450,000 cells/µL", body_style),
            Paragraph(f"<font color='{plt_color.hexval()}'><b>{plt_stat}</b></font>", body_style),
        ],
        [
            Paragraph("<b>Haemoglobin (Hb)</b>", body_style),
            Paragraph(f"<b>{hb:.1f}</b> g/dL", body_style),
            Paragraph("12.0 – 17.5 g/dL", body_style),
            Paragraph(f"<font color='{hb_color.hexval()}'><b>{hb_stat}</b></font>", body_style),
        ],
        [
            Paragraph("<b>PDW</b>", body_style),
            Paragraph(f"<b>{pdw:.1f}</b> %", body_style),
            Paragraph("9.0 – 17.0 %", body_style),
            Paragraph(f"<font color='{pdw_color.hexval()}'><b>{pdw_stat}</b></font>", body_style),
        ],
    ]

    if wbc > 0:
        lab_rows.append(
            [
                Paragraph("<b>WBC Count (TLC)</b>", body_style),
                Paragraph(f"<b>{int(wbc):,}</b> cells/µL", body_style),
                Paragraph("4,000 – 11,000 cells/µL", body_style),
                Paragraph(
                    "<font color='#d97706'><b>Low (Leukopenia)</b></font>" if wbc < 4000 else "Normal Range",
                    body_style,
                ),
            ]
        )

    lab_table = Table(lab_rows, colWidths=[150, 110, 140, 140])
    lab_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    elements.append(lab_table)
    elements.append(Spacer(1, 12))

    # 5. AI Dengue Screening Assessment Box
    elements.append(Paragraph("AI Screening Assessment", section_style))
    pred = data.get("prediction", {})
    risk_level = pred.get("risk_level", "Low")
    prob_pct = round(float(pred.get("probability", 0)) * 100, 1)

    if risk_level == "High":
        box_bg = colors.HexColor("#fef2f2")
        box_border = colors.HexColor("#ef4444")
        risk_color = "#dc2626"
        badge_text = f"HIGH DENGUE RISK ({prob_pct}% Confidence)"
    elif risk_level == "Moderate":
        box_bg = colors.HexColor("#fffbeb")
        box_border = colors.HexColor("#f59e0b")
        risk_color = "#b45309"
        badge_text = f"MODERATE RISK ({prob_pct}% Confidence)"
    else:
        box_bg = colors.HexColor("#f0fdf4")
        box_border = colors.HexColor("#22c55e")
        risk_color = "#15803d"
        badge_text = f"LOW RISK ({prob_pct}% Confidence)"

    assessment_text = (
        f"<font size='12' color='{risk_color}'><b>{badge_text}</b></font><br/><br/>"
        f"<b>Model Summary:</b> {pred.get('message', 'Risk assessment completed.')}<br/>"
        f"<b>Primary Drivers:</b> Based on the model feature analysis, platelet count and haemoglobin "
        f"levels play the most critical role in the classification."
    )

    assessment_table = Table([[Paragraph(assessment_text, body_style)]], colWidths=[540])
    assessment_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), box_bg),
                ("BOX", (0, 0), (-1, -1), 1.5, box_border),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    elements.append(assessment_table)
    elements.append(Spacer(1, 12))

    # 6. Clinical Guidance & Warning Signs
    elements.append(Paragraph("Clinical Guidance & Warning Signs", section_style))
    guidance_text = (
        "• <b>Immediate Emergency Care:</b> Seek urgent medical attention if platelet count drops below 50,000, "
        "or if experiencing persistent vomiting, severe abdominal pain, bleeding gums/nose, or extreme fatigue.<br/>"
        "• <b>Hydration:</b> Maintain high fluid intake (2.5 - 3 Litres/day of water, ORS, or coconut water).<br/>"
        "• <b>Medication Caution:</b> DO NOT take NSAIDs such as Aspirin or Ibuprofen, as they increase bleeding risks. "
        "Consult a qualified doctor before taking any medication."
    )
    guidance_table = Table([[Paragraph(guidance_text, body_style)]], colWidths=[540])
    guidance_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    elements.append(guidance_table)

    # 7. Footer
    elements.append(Spacer(1, 15))
    footer_text = (
        f"Generated by Nexus AI Decision Support System · "
        f"Document ID: {report_info.get('report_id', 'NX-' + datetime.now().strftime('%Y%m%d%H%M%S'))} · "
        f"Confidential Medical Screening Document"
    )
    elements.append(
        Paragraph(
            footer_text,
            ParagraphStyle("Footer", parent=styles["Normal"], fontName="Helvetica", fontSize=7, textColor=colors.HexColor("#94a3b8"), alignment=TA_CENTER),
        )
    )

    doc.build(elements)
    buffer.seek(0)
    return buffer
