"""Excel export for the Module 4 Data Validation Engine report."""
import io
from datetime import datetime

import xlsxwriter

from app.schemas.validation import IssueSeverity, ValidationReport


def generate_validation_report_excel(report: ValidationReport) -> bytes:
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})

    header_fmt = workbook.add_format({
        "bold": True, "bg_color": "#003087", "font_color": "white",
        "border": 1, "align": "center", "valign": "vcenter",
    })
    title_fmt = workbook.add_format({"bold": True, "font_size": 14, "font_color": "#003087"})
    bold_fmt = workbook.add_format({"bold": True})
    error_fmt = workbook.add_format({"bg_color": "#FFEBEE", "border": 1})
    warn_fmt = workbook.add_format({"bg_color": "#FFF8E1", "border": 1})
    cell_fmt = workbook.add_format({"border": 1})

    # -- Summary sheet --
    ws = workbook.add_worksheet("Summary")
    ws.set_column("A:A", 30)
    ws.set_column("B:B", 20)
    ws.write("A1", "IQAC Data Validation Report", title_fmt)
    ws.write("A2", f"Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    ws.write("A3", f"Academic Year: {report.academic_year or 'All years'}")

    rows = [
        ("Records Scanned", report.summary.total_records_scanned),
        ("Total Issues", report.summary.total_issues),
        ("Errors", report.summary.error_count),
        ("Warnings", report.summary.warning_count),
    ]
    r = 5
    for label, value in rows:
        ws.write(r, 0, label, bold_fmt)
        ws.write(r, 1, value)
        r += 1

    r += 1
    ws.write(r, 0, "Issues by Entity", bold_fmt)
    r += 1
    for entity, count in sorted(report.summary.issues_by_entity.items(), key=lambda x: -x[1]):
        ws.write(r, 0, entity)
        ws.write(r, 1, count)
        r += 1

    # -- Issues sheet --
    ws2 = workbook.add_worksheet("Issues")
    columns = ["Severity", "Entity", "Identifier", "Field", "Issue Type", "Message", "Academic Year", "Record ID"]
    for c, col in enumerate(columns):
        ws2.write(0, c, col, header_fmt)
        ws2.set_column(c, c, 22 if col != "Message" else 55)

    for i, issue in enumerate(report.issues, start=1):
        fmt = error_fmt if issue.severity == IssueSeverity.ERROR else warn_fmt
        ws2.write(i, 0, issue.severity.value.upper(), fmt)
        ws2.write(i, 1, issue.entity, fmt)
        ws2.write(i, 2, issue.identifier or "", fmt)
        ws2.write(i, 3, issue.field or "", fmt)
        ws2.write(i, 4, issue.issue_type.value, fmt)
        ws2.write(i, 5, issue.message, fmt)
        ws2.write(i, 6, issue.academic_year or "", fmt)
        ws2.write(i, 7, str(issue.record_id) if issue.record_id else "", fmt)

    workbook.close()
    output.seek(0)
    return output.read()
