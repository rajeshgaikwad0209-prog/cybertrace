"""
CyberTrace PDF Report Generator
===================================
Builds a downloadable PDF summary of a completed assessment using
ReportLab. Contains no credentials, tokens, or unnecessary raw
personal identifiers — only the assessment results the user generated.
"""

import io
from datetime import datetime, timezone

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER

from app.core.scoring import ScoringResult, RISK_LEVEL_COLORS
from app.core.questions import CATEGORY_ORDER, CATEGORIES
from app.core.recommendations import Recommendation

NAVY = colors.HexColor("#0B1C2C")
CYAN = colors.HexColor("#17A2B8")
LIGHT_GRAY = colors.HexColor("#F2F4F6")


def _risk_color(level: str):
    return colors.HexColor(RISK_LEVEL_COLORS.get(level, "#888888"))


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="CTTitle", parent=styles["Title"], textColor=NAVY, fontSize=24, spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="CTSubtitle", parent=styles["Normal"], textColor=colors.HexColor("#555555"),
        fontSize=11, spaceAfter=16
    ))
    styles.add(ParagraphStyle(
        name="CTHeading", parent=styles["Heading2"], textColor=NAVY, spaceBefore=16, spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name="CTBody", parent=styles["Normal"], fontSize=10, leading=14
    ))
    styles.add(ParagraphStyle(
        name="CTSmall", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#777777")
    ))
    styles.add(ParagraphStyle(
        name="CTScoreBig", parent=styles["Normal"], fontSize=36, alignment=TA_CENTER, textColor=NAVY
    ))
    return styles


def generate_pdf_report(
    username: str,
    assessment_date: datetime,
    result: ScoringResult,
    recommendations: list[Recommendation],
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        title="CyberTrace Privacy Assessment Report",
    )
    styles = build_styles()
    story = []

    # --- Header ---
    story.append(Paragraph("CyberTrace", styles["CTTitle"]))
    story.append(Paragraph("Digital Footprint &amp; Privacy Risk Analyzer — Assessment Report", styles["CTSubtitle"]))
    story.append(HRFlowable(width="100%", color=CYAN, thickness=1.2))
    story.append(Spacer(1, 12))

    meta_table = Table([
        ["Report generated:", datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")],
        ["Assessment date:", assessment_date.strftime("%Y-%m-%d %H:%M UTC")],
        ["Account:", username],
    ], colWidths=[1.6 * inch, 4.5 * inch])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555555")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 16))

    # --- Overall score ---
    story.append(Paragraph("Overall Privacy Risk Score", styles["CTHeading"]))
    if result.overall_score is None:
        story.append(Paragraph(
            "No applicable answers were recorded for this assessment, so no score could be calculated.",
            styles["CTBody"]
        ))
    else:
        score_color = _risk_color(result.overall_risk_level)
        score_table = Table([[
            Paragraph(f"{result.overall_score:.1f} / 100", styles["CTScoreBig"]),
        ]], colWidths=[6.1 * inch])
        score_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
            ("BOX", (0, 0), (-1, -1), 1.2, score_color),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 6))
        level_style = ParagraphStyle(
            "LevelStyle", parent=styles["CTBody"], alignment=TA_CENTER,
            textColor=score_color, fontSize=14,
        )
        story.append(Paragraph(f"Risk Level: <b>{result.overall_risk_level}</b>", level_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f"Based on {result.total_applicable} applicable question(s) answered, "
            f"with {result.total_concerns} reported concern(s).",
            styles["CTBody"]
        ))

    story.append(Spacer(1, 10))

    # --- Category breakdown ---
    story.append(Paragraph("Category Breakdown", styles["CTHeading"]))
    cat_rows = [["Category", "Score", "Risk Level", "Applicable Qs", "Concerns"]]
    for cat_key in CATEGORY_ORDER:
        cs = result.category_scores.get(cat_key)
        if cs is None or cs.score is None:
            cat_rows.append([CATEGORIES[cat_key], "N/A", "N/A", "0", "0"])
        else:
            cat_rows.append([
                cs.category_label, f"{cs.score:.1f}", cs.risk_level,
                str(cs.applicable_count), str(cs.concern_count)
            ])
    cat_table = Table(cat_rows, colWidths=[2.3 * inch, 0.8 * inch, 1.1 * inch, 1.1 * inch, 0.9 * inch])
    cat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GRAY]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(cat_table)
    story.append(Spacer(1, 10))

    # --- Recommendations ---
    story.append(Paragraph("Personalized Recommendations", styles["CTHeading"]))
    if not recommendations:
        story.append(Paragraph(
            "No specific concerns were flagged based on your answers. Continue practicing good privacy habits.",
            styles["CTBody"]
        ))
    else:
        for rec in recommendations[:20]:
            rec_style = ParagraphStyle(
                "RecTitle", parent=styles["CTBody"], fontSize=11, textColor=NAVY, spaceBefore=8
            )
            story.append(Paragraph(f"[{rec.priority}] {rec.title}", rec_style))
            story.append(Paragraph(rec.explanation, styles["CTBody"]))
            for step in rec.action_steps:
                story.append(Paragraph(f"&bull; {step}", styles["CTBody"]))
        if len(recommendations) > 20:
            story.append(Paragraph(
                f"...and {len(recommendations) - 20} additional recommendation(s). See the full list in-app.",
                styles["CTSmall"]
            ))

    story.append(PageBreak())

    # --- Methodology & limitations ---
    story.append(Paragraph("Scoring Methodology", styles["CTHeading"]))
    story.append(Paragraph(
        "Each answered question is converted to a normalized risk value between 0 and 1. "
        "That value is multiplied by the question's weight. All weighted values within a "
        "category (or overall) are summed and divided by the total weight of applicable "
        "questions, then multiplied by 100 to produce a 0-100 score. Questions answered "
        "'Not applicable' are excluded from both the numerator and denominator — they are "
        "never treated as safe or risky.",
        styles["CTBody"]
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Assessment Limitations", styles["CTHeading"]))
    story.append(Paragraph(
        "This report reflects information you provided and risk inferred from it. CyberTrace "
        "does not independently verify any data, search data-breach databases, scan the dark "
        "web, or inspect your actual social media accounts. It is an educational self-assessment "
        "tool, not a validated prediction of identity theft risk and not a guarantee of safety. "
        "Scores reflect the current version of this assessment's rules and may change if the "
        "methodology is updated.",
        styles["CTBody"]
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Privacy Improvement Checklist", styles["CTHeading"]))
    checklist_items = [
        "Enable multi-factor authentication on email, banking, and social accounts.",
        "Use unique passwords for each important account (consider a password manager).",
        "Review privacy/visibility settings on your main social accounts.",
        "Remove unnecessary personal contact details from public profiles.",
        "Review third-party app permissions connected to your accounts.",
        "Periodically search your own name to review what's publicly visible.",
    ]
    for item in checklist_items:
        story.append(Paragraph(f"&#9744; {item}", styles["CTBody"]))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#DDDDDD"), thickness=0.75))
    story.append(Paragraph(
        "CyberTrace — Digital Footprint &amp; Privacy Risk Analyzer. "
        "This report contains no passwords, credentials, or session data.",
        styles["CTSmall"]
    ))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes
