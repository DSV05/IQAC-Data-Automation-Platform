"""
Module 8 — Report Generator
=============================
Renders the aggregated report data (from report_data.py) into a styled
multi-sheet Excel workbook. Follows the same xlsxwriter conventions as
Module 4's validation_report.py (brand colors, header formatting).
"""
import io
from datetime import datetime

import xlsxwriter

BRAND_BLUE = "#003087"
BRAND_GOLD = "#C9A227"


def _base_formats(workbook):
    return {
        "title": workbook.add_format({"bold": True, "font_size": 16, "font_color": BRAND_BLUE}),
        "subtitle": workbook.add_format({"font_size": 10, "font_color": "#555555"}),
        "section": workbook.add_format({
            "bold": True, "font_size": 12, "font_color": "white", "bg_color": BRAND_BLUE,
            "align": "left", "valign": "vcenter",
        }),
        "header": workbook.add_format({
            "bold": True, "bg_color": BRAND_GOLD, "font_color": "white",
            "border": 1, "align": "center", "valign": "vcenter",
        }),
        "label": workbook.add_format({"bold": True, "border": 1}),
        "value": workbook.add_format({"border": 1}),
        "cell": workbook.add_format({"border": 1}),
    }


def _write_title(ws, fmts, title: str, academic_year: str):
    ws.merge_range("A1:D1", title, fmts["title"])
    ws.write("A2", f"Ganpat University · IQAC · Generated {datetime.now().strftime('%d/%m/%Y %H:%M')}", fmts["subtitle"])
    ws.write("A3", f"Academic Year: {academic_year}", fmts["subtitle"])


def _write_kv_table(ws, fmts, start_row: int, rows: list[tuple[str, object]]) -> int:
    r = start_row
    for label, value in rows:
        ws.write(r, 0, label, fmts["label"])
        ws.write(r, 1, value, fmts["value"])
        r += 1
    return r


def _write_list_table(ws, fmts, start_row: int, headers: list[str], data_rows: list[list]) -> int:
    r = start_row
    for c, h in enumerate(headers):
        ws.write(r, c, h, fmts["header"])
    r += 1
    for row in data_rows:
        for c, val in enumerate(row):
            ws.write(r, c, val, fmts["cell"])
        r += 1
    return r


def generate_nirf_excel(data: dict) -> bytes:
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    fmts = _base_formats(workbook)

    ws = workbook.add_worksheet("NIRF Summary")
    ws.set_column("A:A", 32)
    ws.set_column("B:D", 20)
    _write_title(ws, fmts, "NIRF Data Summary", data["academic_year"])

    r = 5
    ws.merge_range(r, 0, r, 1, "Faculty & Students", fmts["section"])
    r += 1
    r = _write_kv_table(ws, fmts, r, [
        ("Total Faculty", data["faculty_total"]),
        ("Faculty with PhD", data["faculty_phd"]),
        ("PhD %", f"{data['faculty_phd_pct']}%"),
        ("Total Students", data["student_total"]),
        ("Faculty:Student Ratio", f"1:{data['faculty_student_ratio']}" if data["faculty_student_ratio"] else "N/A"),
    ])

    r += 1
    ws.merge_range(r, 0, r, 1, "Research & Innovation", fmts["section"])
    r += 1
    r = _write_kv_table(ws, fmts, r, [
        ("Publications", data["publications_count"]),
        ("Total Citations", data["publications_citations"]),
        ("Patents Filed", data["patents_filed"]),
        ("Patents Granted", data["patents_granted"]),
        ("Funded Projects", data["funded_projects_count"]),
        ("Funding Received (INR)", data["funded_projects_amount"]),
    ])

    r += 1
    ws.merge_range(r, 0, r, 1, "Outreach & Placements", fmts["section"])
    r += 1
    r = _write_kv_table(ws, fmts, r, [
        ("Students Placed", data["placements_count"]),
        ("Average Package (LPA)", data["placements_avg_package_lpa"]),
        ("Highest Package (LPA)", data["placements_max_package_lpa"]),
        ("Students in Higher Studies", data["higher_studies_count"]),
    ])

    r += 2
    ws.merge_range(r, 0, r, 1, "Faculty by Department", fmts["section"])
    r += 1
    _write_list_table(ws, fmts, r, ["Department", "Faculty Count"],
                       [[d["department"], d["count"]] for d in data["faculty_by_department"]])

    workbook.close()
    return output.getvalue()


def generate_naac_excel(data: dict) -> bytes:
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    fmts = _base_formats(workbook)

    ws = workbook.add_worksheet("NAAC SSR Summary")
    ws.set_column("A:A", 34)
    ws.set_column("B:D", 20)
    _write_title(ws, fmts, "NAAC SSR Data Summary", data["academic_year"])

    r = 5
    sections = [
        ("Criterion I — Curricular Aspects", [
            ("Total Programs", data["criterion_1_curricular"]["programs_total"]),
            ("NBA-Accredited Programs", data["criterion_1_curricular"]["nba_accredited_programs"]),
        ]),
        ("Criterion II — Teaching-Learning & Evaluation", [
            ("Total Faculty", data["criterion_2_teaching_learning"]["faculty_total"]),
            ("Total Students", data["criterion_2_teaching_learning"]["student_total"]),
        ]),
        ("Criterion III — Research, Innovations & Extension", [
            ("Publications", data["criterion_3_research"]["publications"]),
            ("Consultancy Projects", data["criterion_3_research"]["consultancy_projects"]),
            ("Consultancy Amount (INR)", data["criterion_3_research"]["consultancy_amount_inr"]),
            ("SDG Activities", data["criterion_3_research"]["sdg_activities"]),
            ("Extension Activities (Events)", data["criterion_3_research"]["extension_activities"]),
        ]),
        ("Criterion V — Student Support & Progression", [
            ("Students Placed", data["criterion_5_student_support"]["placements"]),
            ("Students in Higher Studies", data["criterion_5_student_support"]["higher_studies"]),
        ]),
        ("Criterion VI — Governance, Leadership & Management", [
            ("Budget Planned (INR)", data["criterion_6_governance"]["budget_planned_inr"]),
            ("Budget Utilized (INR)", data["criterion_6_governance"]["budget_utilized_inr"]),
            ("Active MoUs", data["criterion_6_governance"]["active_mous"]),
        ]),
        ("Criterion VII — Institutional Values & Best Practices", [
            ("Green Initiatives", data["criterion_7_institutional_values"]["green_initiatives"]),
            ("Awards Received", data["criterion_7_institutional_values"]["awards_received"]),
        ]),
    ]
    for title, rows in sections:
        ws.merge_range(r, 0, r, 1, title, fmts["section"])
        r += 1
        r = _write_kv_table(ws, fmts, r, rows)
        r += 1

    r += 1
    ws.merge_range(r, 0, r, 1, "Criterion IV — Infrastructure", fmts["section"])
    r += 1
    r = _write_list_table(ws, fmts, r, ["Facility Type", "Count"],
                           [[f["facility_type"], f["count"]] for f in data["criterion_4_infrastructure"]])

    r += 2
    ws.merge_range(r, 0, r, 2, "Accreditations", fmts["section"])
    r += 1
    _write_list_table(ws, fmts, r, ["Name", "Grade/Score", "Valid Until"],
                       [[a["name"], a["grade"] or "-", a["valid_until"] or "-"] for a in data["accreditations"]])

    workbook.close()
    return output.getvalue()


def generate_aishe_excel(data: dict) -> bytes:
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    fmts = _base_formats(workbook)

    ws = workbook.add_worksheet("AISHE Summary")
    ws.set_column("A:A", 30)
    ws.set_column("B:D", 20)
    _write_title(ws, fmts, "AISHE Institutional Data", data["academic_year"])

    r = 5
    ws.merge_range(r, 0, r, 3, "Programs & Enrollment", fmts["section"])
    r += 1
    r = _write_list_table(
        ws, fmts, r,
        ["Program", "Level", "Sanctioned Intake", "Actual Intake"],
        [[p["name"], p["level"], p["intake_sanctioned"], p["intake_actual"]] for p in data["programs"]],
    )

    r += 2
    ws.merge_range(r, 0, r, 1, "Faculty by Designation", fmts["section"])
    r += 1
    r = _write_list_table(ws, fmts, r, ["Designation", "Count"],
                           [[f["designation"], f["count"]] for f in data["faculty_by_designation"]])

    r += 2
    ws.merge_range(r, 0, r, 1, "Faculty by Gender", fmts["section"])
    r += 1
    r = _write_list_table(ws, fmts, r, ["Gender", "Count"],
                           [[f["gender"], f["count"]] for f in data["faculty_by_gender"]])

    r += 2
    ws.merge_range(r, 0, r, 1, "Students by Gender", fmts["section"])
    r += 1
    r = _write_list_table(ws, fmts, r, ["Gender", "Count"],
                           [[s["gender"], s["count"]] for s in data["students_by_gender"]])

    r += 2
    ws.merge_range(r, 0, r, 1, "Students by Category", fmts["section"])
    r += 1
    _write_list_table(ws, fmts, r, ["Category", "Count"],
                       [[s["category"], s["count"]] for s in data["students_by_category"]])

    workbook.close()
    return output.getvalue()


GENERATORS = {
    "nirf": generate_nirf_excel,
    "naac_ssr": generate_naac_excel,
    "aishe": generate_aishe_excel,
}
