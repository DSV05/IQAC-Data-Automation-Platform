"""
Module 8 — Report Generator
=============================
Renders the same aggregated report data into a PDF using reportlab's
Platypus layer — a cover page plus one table per section, styled with
the Ganpat University brand colors.
"""
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

BRAND_BLUE = colors.HexColor("#003087")
BRAND_GOLD = colors.HexColor("#C9A227")

REPORT_TITLES = {
    "nirf": "NIRF Data Summary",
    "naac_ssr": "NAAC SSR Data Summary",
    "aishe": "AISHE Institutional Data",
}


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle(name="ReportTitle", fontSize=22, textColor=BRAND_BLUE, spaceAfter=6, fontName="Helvetica-Bold"))
    ss.add(ParagraphStyle(name="ReportSubtitle", fontSize=10, textColor=colors.HexColor("#555555"), spaceAfter=2))
    ss.add(ParagraphStyle(name="SectionHeader", fontSize=13, textColor=colors.white, backColor=BRAND_BLUE,
                           spaceBefore=14, spaceAfter=8, leftIndent=6, fontName="Helvetica-Bold"))
    return ss


def _kv_table(rows: list[tuple[str, object]]) -> Table:
    data = [[str(k), str(v)] for k, v in rows]
    t = Table(data, colWidths=[8 * cm, 6 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def _list_table(headers: list[str], rows: list[list], col_widths=None) -> Table:
    data = [headers] + [[str(c) for c in row] for row in rows] if rows else [headers, ["No data available"] + [""] * (len(headers) - 1)]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_GOLD),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
    ]))
    return t


def _cover(story, ss, title: str, academic_year: str):
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph(title, ss["ReportTitle"]))
    story.append(Paragraph("Ganpat University · Internal Quality Assurance Cell (IQAC)", ss["ReportSubtitle"]))
    story.append(Paragraph(f"Academic Year: {academic_year}", ss["ReportSubtitle"]))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ss["ReportSubtitle"]))
    story.append(PageBreak())


def generate_nirf_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    ss = _styles()
    story = []
    _cover(story, ss, REPORT_TITLES["nirf"], data["academic_year"])

    story.append(Paragraph("Faculty &amp; Students", ss["SectionHeader"]))
    story.append(_kv_table([
        ("Total Faculty", data["faculty_total"]),
        ("Faculty with PhD", data["faculty_phd"]),
        ("PhD %", f"{data['faculty_phd_pct']}%"),
        ("Total Students", data["student_total"]),
        ("Faculty:Student Ratio", f"1:{data['faculty_student_ratio']}" if data["faculty_student_ratio"] else "N/A"),
    ]))

    story.append(Paragraph("Research &amp; Innovation", ss["SectionHeader"]))
    story.append(_kv_table([
        ("Publications", data["publications_count"]),
        ("Total Citations", data["publications_citations"]),
        ("Patents Filed", data["patents_filed"]),
        ("Patents Granted", data["patents_granted"]),
        ("Funded Projects", data["funded_projects_count"]),
        ("Funding Received (INR)", f"{data['funded_projects_amount']:,.0f}"),
    ]))

    story.append(Paragraph("Outreach &amp; Placements", ss["SectionHeader"]))
    story.append(_kv_table([
        ("Students Placed", data["placements_count"]),
        ("Average Package (LPA)", data["placements_avg_package_lpa"]),
        ("Highest Package (LPA)", data["placements_max_package_lpa"]),
        ("Students in Higher Studies", data["higher_studies_count"]),
    ]))

    story.append(Paragraph("Faculty by Department", ss["SectionHeader"]))
    story.append(_list_table(
        ["Department", "Faculty Count"],
        [[d["department"], d["count"]] for d in data["faculty_by_department"]],
    ))

    doc.build(story)
    return buf.getvalue()


def generate_naac_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    ss = _styles()
    story = []
    _cover(story, ss, REPORT_TITLES["naac_ssr"], data["academic_year"])

    story.append(Paragraph("Criterion I — Curricular Aspects", ss["SectionHeader"]))
    story.append(_kv_table(list(data["criterion_1_curricular"].items())))

    story.append(Paragraph("Criterion II — Teaching-Learning &amp; Evaluation", ss["SectionHeader"]))
    story.append(_kv_table(list(data["criterion_2_teaching_learning"].items())))

    story.append(Paragraph("Criterion III — Research, Innovations &amp; Extension", ss["SectionHeader"]))
    story.append(_kv_table(list(data["criterion_3_research"].items())))

    story.append(Paragraph("Criterion IV — Infrastructure", ss["SectionHeader"]))
    story.append(_list_table(
        ["Facility Type", "Count"],
        [[f["facility_type"], f["count"]] for f in data["criterion_4_infrastructure"]],
    ))

    story.append(Paragraph("Criterion V — Student Support &amp; Progression", ss["SectionHeader"]))
    story.append(_kv_table(list(data["criterion_5_student_support"].items())))

    story.append(Paragraph("Criterion VI — Governance, Leadership &amp; Management", ss["SectionHeader"]))
    story.append(_kv_table(list(data["criterion_6_governance"].items())))

    story.append(Paragraph("Criterion VII — Institutional Values &amp; Best Practices", ss["SectionHeader"]))
    story.append(_kv_table(list(data["criterion_7_institutional_values"].items())))

    story.append(Paragraph("Accreditations", ss["SectionHeader"]))
    story.append(_list_table(
        ["Name", "Grade/Score", "Valid Until"],
        [[a["name"], a["grade"] or "-", a["valid_until"] or "-"] for a in data["accreditations"]],
    ))

    doc.build(story)
    return buf.getvalue()


def generate_aishe_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    ss = _styles()
    story = []
    _cover(story, ss, REPORT_TITLES["aishe"], data["academic_year"])

    story.append(Paragraph("Programs &amp; Enrollment", ss["SectionHeader"]))
    story.append(_list_table(
        ["Program", "Level", "Sanctioned", "Actual"],
        [[p["name"], p["level"], p["intake_sanctioned"], p["intake_actual"]] for p in data["programs"]],
        col_widths=[7 * cm, 3 * cm, 2.5 * cm, 2.5 * cm],
    ))

    story.append(Paragraph("Faculty by Designation", ss["SectionHeader"]))
    story.append(_list_table(
        ["Designation", "Count"],
        [[f["designation"], f["count"]] for f in data["faculty_by_designation"]],
    ))

    story.append(Paragraph("Faculty by Gender", ss["SectionHeader"]))
    story.append(_list_table(
        ["Gender", "Count"],
        [[f["gender"], f["count"]] for f in data["faculty_by_gender"]],
    ))

    story.append(Paragraph("Students by Gender", ss["SectionHeader"]))
    story.append(_list_table(
        ["Gender", "Count"],
        [[s["gender"], s["count"]] for s in data["students_by_gender"]],
    ))

    story.append(Paragraph("Students by Category", ss["SectionHeader"]))
    story.append(_list_table(
        ["Category", "Count"],
        [[s["category"], s["count"]] for s in data["students_by_category"]],
    ))

    doc.build(story)
    return buf.getvalue()


GENERATORS = {
    "naac_ssr": generate_naac_pdf,
    "aishe": generate_aishe_pdf,
}
