"""Official NIRF 2026 workbook population.

The workbook in ``app/assets/nirf`` is deliberately treated as an immutable
source document.  This module only writes values into its input cells; it does
not recreate sheets, styles, merges, validations, or formulas.
"""
from __future__ import annotations

from copy import copy
from datetime import date
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.awards import Accreditation, Consultancy
from app.models.faculty import Faculty
from app.models.institutional import Budget, Event
from app.models.placement import HigherStudy, Placement
from app.models.research import FundedProject, Patent, ResearchPublication
from app.models.student import Program, Student
from app.models.user import Department

TEMPLATE_PATH = Path(__file__).resolve().parents[1] / "assets" / "nirf" / "1_GUNI_NIRF_2026_DRAFT.xlsx"

# This is the central, reviewable master-data → template mapping.  Values that
# need grouping/aggregation are implemented by the named population helpers.
NIRF_FIELD_MAPPING = {
    "FACULTY LIST": {
        "employee_id": "B", "institute": "C", "department.name": "D", "full_name": "E",
        "age(date_of_birth)": "F", "designation": "G", "gender": "H", "date_of_birth": "I",
        "qualification": "J", "pan_number": "K", "experience_teaching_months": "L",
        "experience_industry_months": "M", "date_of_joining": "Q", "date_of_leaving": "R",
        "employment_type": "S",
    },
    "PLACEMENT DATA": {
        "company_name": "B", "academic_year": "C", "students_placed": "D",
        "maximum_salary_inr": "E", "minimum_salary_inr": "F", "median_salary_inr": "G",
    },
    "NIRF Data": {
        "faculty totals": "B7:B9", "program intake": "B14:G23", "student demographics": "B27:M36",
        "placement and higher studies": "B51:L80", "financial resources": "B84:D93",
        "publications": "B97:C98", "patents": "B102:C104", "sponsored projects": "B108:E110",
        "consultancy": "B114:E116", "development programmes": "B120:E122", "naac accreditation": "B145:B148",
    },
}


def _enum(value):
    return value.value if hasattr(value, "value") else value


def _title(value: object | None) -> str | None:
    return str(value).replace("_", " ").title() if value is not None else None


def _age(dob: date | None) -> int | None:
    if not dob:
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _copy_row_style(ws, source_row: int, target_row: int, columns: int) -> None:
    """Extend roster tables without changing their headers or existing cells."""
    for column in range(1, columns + 1):
        src, target = ws.cell(source_row, column), ws.cell(target_row, column)
        if src.has_style:
            target._style = copy(src._style)
        if src.number_format:
            target.number_format = src.number_format
        if src.alignment:
            target.alignment = copy(src.alignment)


async def generate_nirf_2026_excel(db: AsyncSession, academic_year: str) -> bytes:
    """Fill a copy of the official NIRF workbook with year-scoped master data."""
    if not TEMPLATE_PATH.is_file():
        raise FileNotFoundError(f"Official NIRF template is missing: {TEMPLATE_PATH}")

    wb = load_workbook(TEMPLATE_PATH, data_only=False)
    main, faculty_ws, placement_ws = wb["NIRF Data"], wb["FACULTY LIST"], wb["PLACEMENT DATA"]

    faculty_rows = (await db.execute(
        select(Faculty, Department.name).join(Department, Faculty.department_id == Department.id)
        .where(Faculty.academic_year == academic_year).order_by(Faculty.full_name)
    )).all()
    programs = (await db.execute(
        select(Program).where(Program.academic_year == academic_year, Program.is_active == True)  # noqa: E712
    )).scalars().all()
    students = (await db.execute(
        select(Student).where(Student.academic_year == academic_year, Student.is_active == True)  # noqa: E712
    )).scalars().all()
    placements = (await db.execute(select(Placement).where(Placement.academic_year == academic_year))).scalars().all()
    higher_studies = (await db.execute(select(HigherStudy).where(HigherStudy.academic_year == academic_year))).scalars().all()

    # Faculty detail and roster.
    active_faculty = [(faculty, dept) for faculty, dept in faculty_rows if faculty.is_active]
    main["B7"] = len(active_faculty)
    main["B8"] = sum(_enum(f.gender) == "female" for f, _ in active_faculty)
    main["B9"] = sum(bool(f.phd_awarded) for f, _ in active_faculty)
    for index, (faculty, department) in enumerate(faculty_rows, start=3):
        if index > faculty_ws.max_row:
            _copy_row_style(faculty_ws, 3, index, 19)
        values = [index - 2, faculty.employee_id, faculty.institute, department, faculty.full_name,
                  _age(faculty.date_of_birth), _title(_enum(faculty.designation)), _title(_enum(faculty.gender)),
                  faculty.date_of_birth, _title(_enum(faculty.qualification)), faculty.pan_number,
                  round((faculty.experience_teaching or 0) * 12), round((faculty.experience_industry or 0) * 12),
                  None, "Yes" if faculty.is_active else "No", "Yes" if faculty.is_active else "No",
                  faculty.date_of_joining, faculty.date_of_leaving, _title(_enum(faculty.employment_type))]
        for col, value in enumerate(values, 1):
            if value is not None:
                faculty_ws.cell(index, col).value = value

    # Intake and current student-strength grids use exact NIRF program categories.
    category_rows = {("ug", 6): 14, ("ug", 5): 15, ("ug", 4): 16, ("ug", 3): 17,
                     ("pg", 3): 18, ("pg", 2): 19, ("pg", 1): 20, ("diploma", 3): 22}
    student_category_rows = {key: row + 13 for key, row in category_rows.items()}
    program_by_id = {program.id: program for program in programs}
    for program in programs:
        row = category_rows.get((_enum(program.level), program.duration_years), 23)
        main.cell(row, 2).value = (main.cell(row, 2).value or 0) + (program.intake_sanctioned or 0)
    for student in students:
        program = program_by_id.get(student.program_id)
        if not program:
            continue
        row = student_category_rows.get((_enum(program.level), program.duration_years), 36)
        female = _enum(student.gender) == "female"
        main.cell(row, 2 if not female else 3).value = (main.cell(row, 2 if not female else 3).value or 0) + 1
        main.cell(row, 4).value = (main.cell(row, 4).value or 0) + 1
        domicile = (student.state_of_domicile or "").strip().lower()
        main.cell(row, 5 if domicile in {"gujarat", "gj"} else 6).value = (main.cell(row, 5 if domicile in {"gujarat", "gj"} else 6).value or 0) + 1
        if _enum(student.category) == "ews": main.cell(row, 8).value = (main.cell(row, 8).value or 0) + 1
        if _enum(student.category) in {"sc", "st", "obc"}: main.cell(row, 9).value = (main.cell(row, 9).value or 0) + 1

    # Placement summary, grouped by the same program categories as the template.
    outcomes = {program.id: {"placed": [], "higher": 0, "lateral": 0} for program in programs}
    for placement in placements:
        if placement.program_id in outcomes: outcomes[placement.program_id]["placed"].append(placement)
    for higher in higher_studies:
        if higher.program_id in outcomes: outcomes[higher.program_id]["higher"] += 1
    for student in students:
        if student.program_id in outcomes and student.is_lateral: outcomes[student.program_id]["lateral"] += 1
    placement_rows = {("ug", 6): 51, ("ug", 5): 54, ("ug", 4): 57, ("ug", 3): 60,
                      ("pg", 3): 63, ("pg", 2): 66, ("pg", 1): 69, ("diploma", 3): 75}
    for program in programs:
        row = placement_rows.get((_enum(program.level), program.duration_years), 78)
        placed = outcomes[program.id]["placed"]
        salaries = [p.package_lpa * 100000 for p in placed if p.package_lpa is not None]
        values = {2: academic_year, 3: program.intake_sanctioned, 4: program.intake_actual, 5: academic_year,
                  6: outcomes[program.id]["lateral"], 7: academic_year, 8: len(placed) + outcomes[program.id]["higher"],
                  9: len(placed), 10: outcomes[program.id]["higher"], 11: sorted(salaries)[len(salaries)//2] if salaries else None}
        for col, value in values.items():
            if value is not None: main.cell(row, col).value = (main.cell(row, col).value or 0) + value if isinstance(value, (int, float)) else value

    # Roster of company-wise placement figures.
    by_company: dict[str, list[Placement]] = {}
    for placement in placements:
        by_company.setdefault(placement.company_name or "Not specified", []).append(placement)
    for index, (company, rows) in enumerate(sorted(by_company.items()), start=3):
        if index > placement_ws.max_row:
            _copy_row_style(placement_ws, 3, index, 7)
        salaries = [r.package_lpa * 100000 for r in rows if r.package_lpa is not None]
        values = [index - 2, company, academic_year, len(rows), max(salaries) if salaries else None,
                  min(salaries) if salaries else None, sorted(salaries)[len(salaries)//2] if salaries else None]
        for col, value in enumerate(values, 1):
            if value is not None: placement_ws.cell(index, col).value = value

    # Research, patents, sponsored projects, consultancy and accredited status.
    publications = (await db.execute(select(ResearchPublication).where(ResearchPublication.academic_year == academic_year))).scalars().all()
    for row, index_type in ((97, "wos"), (98, "scopus")):
        matches = [p for p in publications if _enum(p.indexing) == index_type]
        main.cell(row, 2).value, main.cell(row, 3).value = len(matches), sum(p.citations or 0 for p in matches)
    for row, year in zip((102, 103, 104), (2024, 2023, 2022)):
        patents = (await db.execute(select(Patent).where(func.extract("year", Patent.filing_date) == year))).scalars().all()
        main.cell(row, 2).value = sum(_enum(p.status) == "published" for p in patents)
        main.cell(row, 3).value = sum(_enum(p.status) == "granted" for p in patents)
    for start_row, model, amount, groups in ((108, FundedProject, FundedProject.amount_received, FundedProject.funding_agency),
                                               (114, Consultancy, Consultancy.amount_inr, Consultancy.client_name)):
        for row, year in zip(range(start_row, start_row + 3), ("2024-25", "2023-24", "2022-23")):
            records = (await db.execute(select(model).where(model.academic_year == year))).scalars().all()
            main.cell(row, 2).value, main.cell(row, 3).value = len(records), len({getattr(r, groups.key) for r in records})
            main.cell(row, 4).value = sum(getattr(r, amount.key) or 0 for r in records)
    naac = (await db.execute(select(Accreditation).where(Accreditation.is_active == True, Accreditation.name.ilike("%NAAC%")))).scalars().first()  # noqa: E712
    if naac:
        main["B145"].value = "Yes"
        main["B146"].value = naac.valid_from
        main["B147"].value = naac.valid_until
        main["B148"].value = naac.grade_score

    output = BytesIO()
    wb.save(output)
    return output.getvalue()
