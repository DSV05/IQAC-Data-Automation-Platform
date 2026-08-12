"""
Error Report Generator
======================
Produces a styled Excel workbook with:
  - Summary sheet: upload stats
  - Errors sheet: row-level errors with original values
  - Valid Data sheet: preview of accepted rows
"""
import io
from datetime import datetime

import xlsxwriter

from app.utils.excel_validator import RowError


def generate_error_report(
    entity_type: str,
    academic_year: str,
    filename: str,
    total_rows: int,
    valid_rows: list[dict],
    errors: list[RowError],
) -> bytes:
    """Returns an Excel file as bytes."""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})

    # ── Formats ───────────────────────────────────────────────────────────────
    header_fmt = workbook.add_format({
        "bold": True, "bg_color": "#003087", "font_color": "white",
        "border": 1, "align": "center", "valign": "vcenter",
    })
    title_fmt = workbook.add_format({
        "bold": True, "font_size": 14, "font_color": "#003087",
    })
    good_fmt = workbook.add_format({"bg_color": "#E8F5E9", "border": 1})
    bad_fmt  = workbook.add_format({"bg_color": "#FFEBEE", "border": 1})
    warn_fmt = workbook.add_format({"bg_color": "#FFF8E1", "border": 1})
    cell_fmt = workbook.add_format({"border": 1})
    bold_fmt = workbook.add_format({"bold": True})

    # ── Sheet 1: Summary ──────────────────────────────────────────────────────
    ws_summary = workbook.add_worksheet("Summary")
    ws_summary.set_column("A:A", 30)
    ws_summary.set_column("B:B", 20)

    ws_summary.write("A1", "IQAC Upload Validation Report", title_fmt)
    ws_summary.write("A2", f"Generated: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

    data = [
        ("Entity Type",      entity_type.title()),
        ("Academic Year",    academic_year),
        ("Original File",    filename),
        ("Total Rows",       total_rows),
        ("Valid Rows",       len(valid_rows)),
        ("Error Rows",       len(errors)),
        ("Success Rate",     f"{round(len(valid_rows)/max(total_rows,1)*100, 1)}%"),
    ]
    for i, (label, value) in enumerate(data, start=4):
        ws_summary.write(i, 0, label, bold_fmt)
        fmt = good_fmt if "Valid" in label else (bad_fmt if "Error" in label else cell_fmt)
        ws_summary.write(i, 1, value, fmt)

    # ── Sheet 2: Errors ───────────────────────────────────────────────────────
    ws_errors = workbook.add_worksheet("Validation Errors")
    ws_errors.freeze_panes(1, 0)
    ws_errors.set_column("A:A", 8)
    ws_errors.set_column("B:B", 25)
    ws_errors.set_column("C:C", 30)
    ws_errors.set_column("D:D", 45)

    error_headers = ["Row", "Field", "Value Found", "Error Message"]
    for col, h in enumerate(error_headers):
        ws_errors.write(0, col, h, header_fmt)

    for row_idx, err in enumerate(errors, start=1):
        ws_errors.write(row_idx, 0, err.row,   bad_fmt)
        ws_errors.write(row_idx, 1, err.field,  bad_fmt)
        ws_errors.write(row_idx, 2, str(err.value) if err.value is not None else "", bad_fmt)
        ws_errors.write(row_idx, 3, err.error,  bad_fmt)

    if not errors:
        ws_errors.write(1, 0, "No errors found — all rows are valid.", good_fmt)

    # ── Sheet 3: Valid Rows Preview ───────────────────────────────────────────
    ws_valid = workbook.add_worksheet("Valid Rows (Preview)")
    ws_valid.freeze_panes(1, 0)

    if valid_rows:
        preview = valid_rows[:500]  # cap at 500 for performance
        cols = [c for c in preview[0].keys() if c != "academic_year"]
        for col_idx, col_name in enumerate(cols):
            ws_valid.write(0, col_idx, col_name.replace("_", " ").title(), header_fmt)
            ws_valid.set_column(col_idx, col_idx, 18)

        for row_idx, row in enumerate(preview, start=1):
            for col_idx, col_name in enumerate(cols):
                val = row.get(col_name, "")
                if hasattr(val, "isoformat"):
                    val = val.isoformat()
                ws_valid.write(row_idx, col_idx, val if val is not None else "", good_fmt)

        if len(valid_rows) > 500:
            ws_valid.write(len(preview) + 2, 0,
                f"(Showing first 500 of {len(valid_rows)} valid rows)", warn_fmt)

    workbook.close()
    return output.getvalue()
