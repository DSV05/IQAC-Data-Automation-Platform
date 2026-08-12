"""
Module 9 — Excel Auto-Fill
============================
Loads an uploaded .xlsx template with openpyxl (preserving every style,
merged cell, column width, and formula that isn't itself a placeholder),
finds every {{token}} in every cell across every sheet, and replaces it
with the matching value from the token registry.

Two replacement modes, chosen automatically per cell:
  - Whole-cell match ("{{nirf.faculty_total}}" and nothing else): the
    cell's value is replaced directly, preserving its native type (int/
    float) so existing number formatting (e.g. "#,##0" or "0.0%") still
    applies correctly.
  - Embedded match ("Total: {{nirf.faculty_total}} faculty"): the token
    is substituted as text within the larger string.

Unknown tokens are left in place (untouched, visible as {{...}}) and
reported back so the person filling the template knows what wasn't found.
"""
import io
import re

TOKEN_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


class ExcelAutoFillError(Exception):
    pass


def _format_value(value: object) -> object:
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return round(value, 2)
    return value


def find_tokens(file_bytes: bytes) -> set[str]:
    """Returns every distinct {{token}} name referenced anywhere in the workbook."""
    from openpyxl import load_workbook

    try:
        wb = load_workbook(io.BytesIO(file_bytes), data_only=False)
    except Exception as exc:  # noqa: BLE001
        raise ExcelAutoFillError(f"Could not read this file as an Excel workbook: {exc}") from exc

    found: set[str] = set()
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str):
                    found.update(TOKEN_RE.findall(cell.value))
    return found


def fill_template(file_bytes: bytes, token_values: dict[str, object]) -> tuple[bytes, int, list[str]]:
    """
    Returns (filled_workbook_bytes, tokens_filled_count, missing_token_names).
    A token counts as "filled" once per cell it appears in, not per occurrence
    within a cell's text.
    """
    from openpyxl import load_workbook

    try:
        wb = load_workbook(io.BytesIO(file_bytes), data_only=False)
    except Exception as exc:  # noqa: BLE001
        raise ExcelAutoFillError(f"Could not read this file as an Excel workbook: {exc}") from exc

    filled_count = 0
    missing: set[str] = set()

    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if not isinstance(cell.value, str):
                    continue
                matches = TOKEN_RE.findall(cell.value)
                if not matches:
                    continue

                whole_cell_match = TOKEN_RE.fullmatch(cell.value.strip())
                cell_had_known_token = False

                if whole_cell_match:
                    token_name = whole_cell_match.group(1)
                    if token_name in token_values:
                        cell.value = _format_value(token_values[token_name])
                        cell_had_known_token = True
                    else:
                        missing.add(token_name)
                else:
                    new_text = cell.value
                    for token_name in matches:
                        if token_name in token_values:
                            new_text = new_text.replace(
                                f"{{{{{token_name}}}}}", str(_format_value(token_values[token_name]))
                            )
                            cell_had_known_token = True
                        else:
                            missing.add(token_name)
                    cell.value = new_text

                if cell_had_known_token:
                    filled_count += 1

    output = io.BytesIO()
    wb.save(output)
    return output.getvalue(), filled_count, sorted(missing)
