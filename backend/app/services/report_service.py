from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)


# ============================================================
# INDIVIDUAL WORKER SAFETY REPORT
# ============================================================

def generate_person_report(person_id, violations, output_path):
    """
    Generate an individual worker safety report.

    The report contains all violations associated
    with the specified person ID.
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        leading=26,
        spaceAfter=5,
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=18,
    )

    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "ReportNormal",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=14,
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
    )

    story = []

    # ---------------------------------------------------------
    # CALCULATE SUMMARY
    # ---------------------------------------------------------

    total_violations = len(violations)

    high_risk = sum(
        1 for v in violations
        if float(v.confidence) >= 0.80
    )

    medium_risk = sum(
        1 for v in violations
        if 0.50 <= float(v.confidence) < 0.80
    )

    low_risk = sum(
        1 for v in violations
        if float(v.confidence) < 0.50
    )

    if total_violations > 0:
        average_confidence = (
            sum(float(v.confidence) for v in violations)
            / total_violations
        )
    else:
        average_confidence = 0

    # ---------------------------------------------------------
    # REPORT HEADER
    # ---------------------------------------------------------

    story.append(
        Paragraph("SKYGUARD AI", title_style)
    )

    story.append(
        Paragraph(
            "INDIVIDUAL WORKER SAFETY REPORT",
            subtitle_style,
        )
    )

    # ---------------------------------------------------------
    # WORKER IDENTIFICATION
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "1. Worker Identification",
            section_style,
        )
    )

    worker_data = [
        ["Person ID", str(person_id)],
        ["Name", "Not available"],
        ["Employee ID", str(person_id)],
        ["Department", "Not available"],
        ["Monitoring Status", "Active"],
    ]

    worker_table = Table(
        worker_data,
        colWidths=[55 * mm, 105 * mm],
    )

    worker_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#EAF2F8"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (1, 0),
                    (1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(worker_table)

    # ---------------------------------------------------------
    # SAFETY SUMMARY
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "2. Safety Summary",
            section_style,
        )
    )

    if high_risk > 0:
        overall_status = "REQUIRES ATTENTION"
    elif total_violations > 0:
        overall_status = "MONITOR"
    else:
        overall_status = "NO VIOLATIONS"

    summary_data = [
        ["Total Violations", str(total_violations)],
        ["High Risk", str(high_risk)],
        ["Medium Risk", str(medium_risk)],
        ["Low Risk", str(low_risk)],
        [
            "Average AI Confidence",
            f"{average_confidence * 100:.1f}%",
        ],
        ["Overall Status", overall_status],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[75 * mm, 85 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#F8FAFC"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (1, 0),
                    (1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(summary_table)

    # ---------------------------------------------------------
    # VIOLATION HISTORY
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "3. Violation History",
            section_style,
        )
    )

    history_data = [
        [
            "Violation",
            "Type",
            "Confidence",
            "Date & Time",
        ]
    ]

    for violation in violations:

        timestamp = violation.timestamp

        if isinstance(timestamp, datetime):
            formatted_time = timestamp.strftime(
                "%d %b %Y\n%I:%M:%S %p"
            )
        else:
            formatted_time = str(timestamp)

        violation_name = (
            str(violation.type)
            .replace("-", " ")
            .title()
        )

        history_data.append(
            [
                str(violation.id),
                violation_name,
                f"{float(violation.confidence) * 100:.1f}%",
                formatted_time,
            ]
        )

    history_table = Table(
        history_data,
        colWidths=[
            20 * mm,
            50 * mm,
            35 * mm,
            55 * mm,
        ],
        repeatRows=1,
    )

    history_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1F2937"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(history_table)

    # ---------------------------------------------------------
    # DETAILED VIOLATIONS
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "4. Detailed Violation Evidence",
            section_style,
        )
    )

    for index, violation in enumerate(violations, start=1):

        violation_name = (
            str(violation.type)
            .replace("-", " ")
            .title()
        )

        confidence = float(violation.confidence)

        if confidence >= 0.80:
            risk_level = "HIGH"
        elif confidence >= 0.50:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        story.append(
            Paragraph(
                f"<b>Violation {index}: {violation_name}</b>",
                normal_style,
            )
        )

        detail_data = [
            ["Violation ID", str(violation.id)],
            ["Risk Level", risk_level],
            [
                "AI Confidence",
                f"{confidence * 100:.1f}%",
            ],
            [
                "Latitude",
                f"{float(violation.latitude):.7f}",
            ],
            [
                "Longitude",
                f"{float(violation.longitude):.7f}",
            ],
            [
                "Timestamp",
                str(violation.timestamp),
            ],
        ]

        detail_table = Table(
            detail_data,
            colWidths=[55 * mm, 105 * mm],
        )

        detail_table.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, -1),
                        colors.HexColor("#F8FAFC"),
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (0, -1),
                        "Helvetica-Bold",
                    ),
                    (
                        "FONTNAME",
                        (1, 0),
                        (1, -1),
                        "Helvetica",
                    ),
                    (
                        "FONTSIZE",
                        (0, 0),
                        (-1, -1),
                        8.5,
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#CBD5E1"),
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        5,
                    ),
                ]
            )
        )

        story.append(detail_table)
        story.append(Spacer(1, 4 * mm))

        # -----------------------------------------------------
        # EVIDENCE IMAGE
        # -----------------------------------------------------

        image_path = Path("snapshots") / str(
            violation.image_url
        )

        if image_path.exists():

            try:
                evidence_image = Image(
                    str(image_path),
                    width=110 * mm,
                    height=75 * mm,
                    kind="proportional",
                )

                story.append(
                    Paragraph(
                        "<b>Evidence Snapshot</b>",
                        normal_style,
                    )
                )

                story.append(evidence_image)

            except Exception:

                story.append(
                    Paragraph(
                        "Evidence image could not be embedded.",
                        small_style,
                    )
                )

        else:

            story.append(
                Paragraph(
                    f"Evidence image not available: "
                    f"{violation.image_url}",
                    small_style,
                )
            )

        story.append(Spacer(1, 8 * mm))

    # ---------------------------------------------------------
    # OVERALL ASSESSMENT
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "5. Overall Safety Assessment",
            section_style,
        )
    )

    if total_violations == 0:

        assessment = (
            f"No safety violations were recorded for "
            f"Person {person_id} during the monitored period."
        )

    else:

        assessment = (
            f"Person <b>{person_id}</b> was associated with "
            f"<b>{total_violations}</b> safety violation(s) "
            f"during the monitored period. "
            f"The system recorded <b>{high_risk}</b> high-risk, "
            f"<b>{medium_risk}</b> medium-risk and "
            f"<b>{low_risk}</b> low-risk event(s). "
            f"The average AI detection confidence was "
            f"<b>{average_confidence * 100:.1f}%</b>. "
            f"The recorded events should be reviewed according "
            f"to the site's safety procedures."
        )

    story.append(
        Paragraph(
            assessment,
            normal_style,
        )
    )

    # ---------------------------------------------------------
    # FOOTER
    # ---------------------------------------------------------

    story.append(Spacer(1, 15 * mm))

    story.append(
        Paragraph(
            "Generated automatically by SkyGuard AI — "
            "AI-Powered Workplace Safety Monitoring System",
            ParagraphStyle(
                "Footer",
                parent=normal_style,
                alignment=TA_CENTER,
                fontSize=8,
                textColor=colors.grey,
            ),
        )
    )

    doc.build(story)

    return str(output_path)


# ============================================================
# OVERALL SITE SAFETY REPORT
# ============================================================

def generate_overall_report(violations, output_path):
    """
    Generate an overall SkyGuard AI workplace safety report.

    This report includes:
    - Total violations
    - Workers affected
    - Risk distribution
    - Average AI confidence
    - Worker-wise summary
    - Complete violation history
    - Overall safety assessment
    """

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "OverallReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        leading=26,
        spaceAfter=5,
    )

    subtitle_style = ParagraphStyle(
        "OverallReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=18,
    )

    section_style = ParagraphStyle(
        "OverallSectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=8,
    )

    normal_style = ParagraphStyle(
        "OverallNormal",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=14,
    )

    story = []

    # ---------------------------------------------------------
    # CALCULATE SUMMARY
    # ---------------------------------------------------------

    total_violations = len(violations)

    high_risk = sum(
        1 for v in violations
        if float(v.confidence) >= 0.80
    )

    medium_risk = sum(
        1 for v in violations
        if 0.50 <= float(v.confidence) < 0.80
    )

    low_risk = sum(
        1 for v in violations
        if float(v.confidence) < 0.50
    )

    workers = sorted(
        set(
            str(v.person_id)
            for v in violations
            if getattr(v, "person_id", None)
            and str(v.person_id) != "UNKNOWN"
        )
    )

    average_confidence = (
        sum(float(v.confidence) for v in violations)
        / total_violations
        if total_violations
        else 0
    )

    # ---------------------------------------------------------
    # REPORT HEADER
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "SKYGUARD AI",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "OVERALL WORKPLACE SAFETY REPORT",
            subtitle_style,
        )
    )

    # ---------------------------------------------------------
    # SITE SAFETY SUMMARY
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "1. Site Safety Summary",
            section_style,
        )
    )

    if high_risk > 0:
        overall_status = "REQUIRES ATTENTION"
    elif total_violations > 0:
        overall_status = "MONITOR"
    else:
        overall_status = "NO VIOLATIONS"

    summary_data = [
        ["Total Violations", str(total_violations)],
        ["Workers Affected", str(len(workers))],
        ["High Risk", str(high_risk)],
        ["Medium Risk", str(medium_risk)],
        ["Low Risk", str(low_risk)],
        [
            "Average AI Confidence",
            f"{average_confidence * 100:.1f}%",
        ],
        ["Overall Status", overall_status],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[75 * mm, 85 * mm],
    )

    summary_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#EAF2F8"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (0, -1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (1, 0),
                    (1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
            ]
        )
    )

    story.append(summary_table)

    # ---------------------------------------------------------
    # WORKER-WISE SUMMARY
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "2. Worker-wise Safety Summary",
            section_style,
        )
    )

    worker_data = [
        [
            "Person ID",
            "Violations",
            "High Risk",
            "Latest Violation",
        ]
    ]

    for person_id in workers:

        person_violations = [
            v for v in violations
            if str(v.person_id) == person_id
        ]

        person_high_risk = sum(
            1 for v in person_violations
            if float(v.confidence) >= 0.80
        )

        latest = max(
            person_violations,
            key=lambda v: v.timestamp
        )

        latest_type = (
            str(latest.type)
            .replace("-", " ")
            .title()
        )

        worker_data.append(
            [
                person_id,
                str(len(person_violations)),
                str(person_high_risk),
                latest_type,
            ]
        )

    if len(worker_data) == 1:
        worker_data.append(
            [
                "No identified workers",
                "0",
                "0",
                "N/A",
            ]
        )

    worker_table = Table(
        worker_data,
        colWidths=[
            35 * mm,
            35 * mm,
            35 * mm,
            55 * mm,
        ],
        repeatRows=1,
    )

    worker_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1F2937"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(worker_table)

    # ---------------------------------------------------------
    # VIOLATION HISTORY
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "3. Violation History",
            section_style,
        )
    )

    history_data = [
        [
            "ID",
            "Person",
            "Violation",
            "Confidence",
            "Date & Time",
        ]
    ]

    for violation in violations:

        violation_name = (
            str(violation.type)
            .replace("-", " ")
            .title()
        )

        timestamp = violation.timestamp

        if isinstance(timestamp, datetime):
            formatted_time = timestamp.strftime(
                "%d %b %Y %I:%M:%S %p"
            )
        else:
            formatted_time = str(timestamp)

        history_data.append(
            [
                str(violation.id),
                str(violation.person_id),
                violation_name,
                f"{float(violation.confidence) * 100:.1f}%",
                formatted_time,
            ]
        )

    if len(history_data) == 1:
        history_data.append(
            [
                "-",
                "-",
                "No violations",
                "-",
                "-",
            ]
        )

    history_table = Table(
        history_data,
        colWidths=[
            15 * mm,
            25 * mm,
            40 * mm,
            30 * mm,
            50 * mm,
        ],
        repeatRows=1,
    )

    history_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#1F2937"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    7.5,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(history_table)

    # ---------------------------------------------------------
    # OVERALL ASSESSMENT
    # ---------------------------------------------------------

    story.append(
        Paragraph(
            "4. Overall Safety Assessment",
            section_style,
        )
    )

    if total_violations == 0:

        assessment = (
            "No safety violations were recorded during "
            "the monitored period."
        )

    else:

        assessment = (
            f"SkyGuard AI recorded <b>{total_violations}</b> "
            f"safety violation(s) involving "
            f"<b>{len(workers)}</b> identified worker(s). "
            f"The system detected <b>{high_risk}</b> high-risk, "
            f"<b>{medium_risk}</b> medium-risk and "
            f"<b>{low_risk}</b> low-risk event(s). "
            f"The average AI detection confidence was "
            f"<b>{average_confidence * 100:.1f}%</b>. "
            f"The recorded events should be reviewed according "
            f"to the site's safety procedures."
        )

    story.append(
        Paragraph(
            assessment,
            normal_style,
        )
    )

    # ---------------------------------------------------------
    # FOOTER
    # ---------------------------------------------------------

    story.append(Spacer(1, 15 * mm))

    story.append(
        Paragraph(
            "Generated automatically by SkyGuard AI — "
            "AI-Powered Workplace Safety Monitoring System",
            ParagraphStyle(
                "OverallFooter",
                parent=normal_style,
                alignment=TA_CENTER,
                fontSize=8,
                textColor=colors.grey,
            ),
        )
    )

    doc.build(story)

    return str(output_path)