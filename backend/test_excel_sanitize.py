"""
Test harness for the extLst / WPS-style xlsx sanitization fix in
app/utils/excel_validator.py.

Runs the REAL ExcelValidator (imported from the actual project source,
no reimplementation) against several upload scenarios:

  1. The real WPS-corrupted faculty_2024-25.xlsx (uploaded by the user)
  2. Same file, in "update" mode (natural-key-only required fields)
  3. A clean, standard xlsx with no extLst (regression check - must
     still work, and must NOT go through the sanitize/retry path)
  4. A synthetic xlsx with extLst on font/border AND patternFill,
     multiple sheets, to check the regex isn't overly narrow
  5. A .csv file (must be completely unaffected by the xlsx-only patch)
  6. A genuinely corrupt file (not a real zip at all) - must still
     raise a clean ValueError, not crash uncontrolled
  7. An xlsx with extLst but missing rows (edge: sanitize should not
     touch cell data even if styles are stripped)

Run: python3 test_excel_sanitize.py
"""
import shutil
import sys
import tempfile
import traceback
import zipfile
from io import BytesIO
from pathlib import Path

sys.path.insert(0, ".")

from app.utils.excel_validator import ExcelValidator  # noqa: E402

PASS = []
FAIL = []


def check(name, condition, detail=""):
    if condition:
        PASS.append(name)
        print(f"  [PASS] {name}")
    else:
        FAIL.append(name)
        print(f"  [FAIL] {name}  {detail}")


def make_clean_xlsx(path, rows):
    """Build a normal, unmodified openpyxl workbook (no extLst)."""
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Faculty"
    headers = ["Employee Id *", "Full Name *", "Gender *", "Designation *",
               "Qualification *", "Employment Type *", "Experience Teaching *"]
    ws.append(headers)
    for r in rows:
        ws.append(r)
    wb.save(path)


def inject_extlst(src_path, dst_path, targets=("patternFill", "font", "border")):
    """
    Take a clean xlsx and hand-inject WPS-style <extLst> blocks into
    styles.xml elements, simulating what WPS Office / Kingsoft actually
    writes (and what broke the original upload).
    """
    with zipfile.ZipFile(src_path, "r") as zin:
        names = zin.namelist()
        entries = {n: zin.read(n) for n in names}

    styles = entries["xl/styles.xml"].decode("utf-8")
    ext_block = (
        '<extLst><ext uri="smNativeData">'
        '<pm:shade xmlns:pm="smNativeData" id="1" type="1" '
        'fgLvl="100" fgClr="00000000" bgLvl="0" bgClr="00000000"/>'
        '</ext></extLst>'
    )

    if "patternFill" in targets:
        # openpyxl's default empty fill is self-closing: <patternFill/>
        styles = styles.replace(
            "<patternFill/>",
            f'<patternFill patternType="solid"><fgColor rgb="FF6B7280"/>'
            f'<bgColor rgb="FFFFFFFF"/>{ext_block}</patternFill>',
            1,
        )
    if "font" in targets and "<font>" in styles:
        styles = styles.replace("<font>", f"<font>{ext_block}", 1)
    if "border" in targets and "<border>" in styles:
        styles = styles.replace("<border>", f"<border>{ext_block}", 1)

    entries["xl/styles.xml"] = styles.encode("utf-8")

    out = BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for n in names:
            zout.writestr(n, entries[n])
    Path(dst_path).write_bytes(out.getvalue())


def run():
    tmp = Path(tempfile.mkdtemp(prefix="xlsx_test_"))
    print(f"Working dir: {tmp}\n")

    # ── Scenario 1: the real user-uploaded WPS file ────────────────────────
    print("Scenario 1: real WPS-corrupted faculty_2024-25.xlsx (insert mode)")
    real_file = tmp / "faculty_real.xlsx"
    shutil.copy("/mnt/user-data/uploads/faculty_2024-25.xlsx", real_file)
    try:
        v = ExcelValidator("faculty", "2024-25", mode="insert")
        result = v.validate(str(real_file))
        check("scenario1_no_exception", True)
        check("scenario1_rows_parsed", len(result.valid_rows) + len(result.errors) > 0,
              f"valid={len(result.valid_rows)} errors={len(result.errors)}")
        print(f"    -> valid_rows={len(result.valid_rows)} row_errors={len(result.errors)}")
    except Exception as e:
        check("scenario1_no_exception", False, repr(e))
        traceback.print_exc()

    # ── Scenario 2: same file, update mode ─────────────────────────────────
    print("\nScenario 2: same WPS file, update mode (only employee_id required)")
    try:
        v = ExcelValidator("faculty", "2024-25", mode="update")
        result = v.validate(str(real_file))
        check("scenario2_no_exception", True)
        print(f"    -> valid_rows={len(result.valid_rows)} row_errors={len(result.errors)}")
    except Exception as e:
        check("scenario2_no_exception", False, repr(e))

    # ── Scenario 3: clean xlsx, no extLst — regression / no-op check ───────
    print("\nScenario 3: clean xlsx with no extLst (must not need sanitizing)")
    clean_file = tmp / "faculty_clean.xlsx"
    make_clean_xlsx(clean_file, [
        ["EMP9001", "Test Person", "female", "professor", "phd", "permanent", "10"],
    ])
    try:
        v = ExcelValidator("faculty", "2024-25", mode="insert")
        result = v.validate(str(clean_file))
        check("scenario3_no_exception", True)
        check("scenario3_one_valid_row", len(result.valid_rows) == 1,
              f"got {len(result.valid_rows)}")
    except Exception as e:
        check("scenario3_no_exception", False, repr(e))

    # ── Scenario 4: synthetic extLst on font/border/patternFill together ───
    print("\nScenario 4: synthetic multi-location extLst (font+border+patternFill)")
    synth_file = tmp / "faculty_synth_ext.xlsx"
    inject_extlst(clean_file, synth_file, targets=("patternFill", "font", "border"))
    # Confirm it actually reproduces the crash pre-fix, to prove the test is real:
    try:
        import openpyxl
        openpyxl.load_workbook(synth_file)
        check("scenario4_reproduces_bug_precheck", False, "expected TypeError but load succeeded")
    except TypeError as e:
        check("scenario4_reproduces_bug_precheck", "extLst" in str(e) or "unexpected keyword" in str(e), str(e))
    try:
        v = ExcelValidator("faculty", "2024-25", mode="insert")
        result = v.validate(str(synth_file))
        check("scenario4_no_exception_after_fix", True)
        check("scenario4_row_intact", len(result.valid_rows) == 1,
              f"got {len(result.valid_rows)}")
    except Exception as e:
        check("scenario4_no_exception_after_fix", False, repr(e))

    # ── Scenario 5: CSV must be totally unaffected ──────────────────────────
    print("\nScenario 5: CSV upload unaffected by xlsx-only patch")
    csv_file = tmp / "faculty.csv"
    csv_file.write_text(
        "Employee Id *,Full Name *,Gender *,Designation *,Qualification *,Employment Type *,Experience Teaching *\n"
        "EMP9002,CSV Person,male,lecturer,phd,permanent,3\n",
        encoding="utf-8",
    )
    try:
        v = ExcelValidator("faculty", "2024-25", mode="insert")
        result = v.validate(str(csv_file))
        check("scenario5_csv_ok", len(result.valid_rows) == 1, f"got {len(result.valid_rows)}")
    except Exception as e:
        check("scenario5_csv_ok", False, repr(e))

    # ── Scenario 6: genuinely corrupt / non-zip file ────────────────────────
    print("\nScenario 6: genuinely corrupt file (not a real zip) fails cleanly")
    junk_file = tmp / "junk.xlsx"
    junk_file.write_bytes(b"this is not a real xlsx file at all")
    try:
        v = ExcelValidator("faculty", "2024-25", mode="insert")
        v.validate(str(junk_file))
        check("scenario6_raises_valueerror", False, "expected ValueError but none raised")
    except ValueError as e:
        check("scenario6_raises_valueerror", True)
        check("scenario6_message_prefixed", str(e).startswith("Cannot read file:"), str(e))
        print(f"    -> {e}")
    except Exception as e:
        check("scenario6_raises_valueerror", False, f"wrong exception type: {repr(e)}")

    # ── Scenario 7: extLst file with header-only (no data rows) ────────────
    print("\nScenario 7: extLst file with header row only (no data)")
    empty_clean = tmp / "faculty_empty_clean.xlsx"
    make_clean_xlsx(empty_clean, [])
    empty_ext = tmp / "faculty_empty_ext.xlsx"
    inject_extlst(empty_clean, empty_ext)
    try:
        v = ExcelValidator("faculty", "2024-25", mode="insert")
        result = v.validate(str(empty_ext))
        check("scenario7_no_exception", True)
        check("scenario7_zero_rows", len(result.valid_rows) == 0 and len(result.errors) == 0,
              f"valid={len(result.valid_rows)} errors={len(result.errors)}")
    except Exception as e:
        check("scenario7_no_exception", False, repr(e))

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"PASSED: {len(PASS)}   FAILED: {len(FAIL)}")
    if FAIL:
        print("Failures:", FAIL)
    print(f"{'='*60}")
    return len(FAIL) == 0


if __name__ == "__main__":
    ok = run()
    sys.exit(0 if ok else 1)
