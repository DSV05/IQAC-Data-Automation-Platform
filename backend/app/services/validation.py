"""
Module 4 — Data Validation Engine
==================================
Runs a suite of rule-based checks across the master data tables and returns
a flat list of ValidationIssue objects. This is read-only: it never mutates
data, it only reports problems so an IQAC Admin / Department Coordinator can
go fix them (or so a future module can auto-fix / block report generation).

Categories of checks:
  1. Duplicates       — same natural identity appearing more than once in a
                         way the DB's unique constraints don't catch
                         (e.g. same email reused across two employee_ids).
  2. Orphan references — FK points at a department that's soft-deleted
                         (is_active=False), or a required parent link
                         is logically inconsistent (department mismatch).
  3. Missing fields    — nullable-in-DB but required for NIRF/NAAC/AISHE
                         submissions.
  4. Logical checks    — date ranges, out-of-bounds values, expired
                         accreditation, etc.

Add a new check by writing a `_check_*` method that appends ValidationIssue
objects to `self.issues`, then registering it in `run()`.
"""
from collections import Counter, defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.faculty import Faculty
from app.models.placement import HigherStudy, Placement
from app.models.research import FundedProject, Patent, ResearchPublication
from app.models.student import Program, Student
from app.models.user import Department
from app.schemas.validation import (
    IssueSeverity,
    IssueType,
    ValidationIssue,
    ValidationReport,
    ValidationSummary,
)


class ValidationEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.issues: list[ValidationIssue] = []
        self._records_scanned = 0

    # -- Public entrypoint -------------------------------------------------

    async def run(self, academic_year: str | None = None) -> ValidationReport:
        self.issues = []
        self._records_scanned = 0

        departments = (await self.db.execute(select(Department))).scalars().all()
        dept_by_id = {d.id: d for d in departments}

        faculty = await self._fetch(Faculty, academic_year)
        students = await self._fetch(Student, academic_year)
        programs = await self._fetch(Program, academic_year)
        placements = await self._fetch(Placement, academic_year)
        higher_studies = await self._fetch(HigherStudy, academic_year)
        publications = await self._fetch(ResearchPublication, academic_year)
        patents = await self._fetch(Patent, academic_year)
        projects = await self._fetch(FundedProject, academic_year)

        program_by_id = {p.id: p for p in programs}

        self._check_orphan_departments(faculty, "faculty", "employee_id", dept_by_id)
        self._check_orphan_departments(students, "students", "enrollment_no", dept_by_id)
        self._check_orphan_departments(programs, "programs", "code", dept_by_id)
        self._check_orphan_departments(placements, "placements", "enrollment_no", dept_by_id)
        self._check_orphan_departments(higher_studies, "higher_studies", "enrollment_no", dept_by_id)
        self._check_orphan_departments(publications, "research_publications", "title", dept_by_id)
        self._check_orphan_departments(patents, "patents", "application_number", dept_by_id)
        self._check_orphan_departments(projects, "funded_projects", "title", dept_by_id)

        self._check_faculty(faculty)
        self._check_students(students, program_by_id)
        self._check_programs(programs)
        self._check_placements(placements, program_by_id)
        self._check_research(publications, patents, projects)

        return self._build_report(academic_year)

    # -- Helpers -------------------------------------------------------------

    async def _fetch(self, model, academic_year: str | None):
        stmt = select(model)
        if academic_year and hasattr(model, "academic_year"):
            stmt = stmt.where(model.academic_year == academic_year)
        rows = (await self.db.execute(stmt)).scalars().all()
        self._records_scanned += len(rows)
        return rows

    def _add(
        self, entity: str, record, severity: IssueSeverity, issue_type: IssueType,
        message: str, field: str | None = None, identifier: str | None = None,
    ):
        self.issues.append(
            ValidationIssue(
                entity=entity,
                record_id=getattr(record, "id", None),
                academic_year=getattr(record, "academic_year", None),
                severity=severity,
                issue_type=issue_type,
                field=field,
                message=message,
                identifier=identifier,
            )
        )

    def _build_report(self, academic_year: str | None) -> ValidationReport:
        by_entity = Counter(i.entity for i in self.issues)
        by_type = Counter(i.issue_type.value for i in self.issues)
        errors = sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)
        warnings = sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)
        summary = ValidationSummary(
            total_records_scanned=self._records_scanned,
            total_issues=len(self.issues),
            error_count=errors,
            warning_count=warnings,
            issues_by_entity=dict(by_entity),
            issues_by_type=dict(by_type),
        )
        # Most severe / most recently added first is fine; sort errors before warnings
        sorted_issues = sorted(self.issues, key=lambda i: 0 if i.severity == IssueSeverity.ERROR else 1)
        return ValidationReport(academic_year=academic_year, summary=summary, issues=sorted_issues)

    # -- Cross-cutting: orphan / inactive department references --------------

    def _check_orphan_departments(self, rows, entity: str, id_field: str, dept_by_id: dict):
        for row in rows:
            dept_id = getattr(row, "department_id", None)
            if dept_id is None:
                continue
            dept = dept_by_id.get(dept_id)
            identifier = str(getattr(row, id_field, row.id))
            if dept is None:
                self._add(
                    entity, row, IssueSeverity.ERROR, IssueType.ORPHAN_REFERENCE,
                    "References a department that no longer exists in the system.",
                    field="department_id", identifier=identifier,
                )
            elif not dept.is_active:
                self._add(
                    entity, row, IssueSeverity.WARNING, IssueType.ORPHAN_REFERENCE,
                    f"Belongs to department '{dept.name}', which is marked inactive.",
                    field="department_id", identifier=identifier,
                )

    # -- Faculty ---------------------------------------------------------------

    def _check_faculty(self, faculty: list[Faculty]):
        seen_email: dict[tuple[str, str], list] = defaultdict(list)
        seen_identity: dict[tuple[str, str], list] = defaultdict(list)

        for f in faculty:
            if f.email:
                seen_email[(f.email.strip().lower(), f.academic_year)].append(f)
            seen_identity[(f.full_name.strip().lower(), f.academic_year)].append(f)

            if f.date_of_joining and f.date_of_leaving and f.date_of_leaving < f.date_of_joining:
                self._add(
                    "faculty", f, IssueSeverity.ERROR, IssueType.INVALID_DATE_RANGE,
                    "Date of leaving is before date of joining.",
                    field="date_of_leaving", identifier=f.employee_id,
                )
            if f.phd_year and not f.phd_awarded:
                self._add(
                    "faculty", f, IssueSeverity.WARNING, IssueType.LOGICAL_INCONSISTENCY,
                    "PhD year is set but 'PhD awarded' is not marked true.",
                    field="phd_awarded", identifier=f.employee_id,
                )
            if f.date_of_leaving and f.is_active:
                self._add(
                    "faculty", f, IssueSeverity.WARNING, IssueType.LOGICAL_INCONSISTENCY,
                    "Has a date of leaving but is still marked active.",
                    field="is_active", identifier=f.employee_id,
                )
            if not f.email and not f.phone:
                self._add(
                    "faculty", f, IssueSeverity.WARNING, IssueType.MISSING_REQUIRED_FIELD,
                    "No email or phone on record — required for NIRF/NAAC faculty rosters.",
                    field="email", identifier=f.employee_id,
                )
            if not f.pan_number:
                self._add(
                    "faculty", f, IssueSeverity.WARNING, IssueType.MISSING_REQUIRED_FIELD,
                    "PAN number is missing.",
                    field="pan_number", identifier=f.employee_id,
                )

        for (email, year), rows in seen_email.items():
            if len(rows) > 1:
                ids = ", ".join(sorted({r.employee_id for r in rows}))
                for r in rows:
                    self._add(
                        "faculty", r, IssueSeverity.ERROR, IssueType.DUPLICATE,
                        f"Email '{email}' is shared by multiple employee IDs in {year}: {ids}.",
                        field="email", identifier=r.employee_id,
                    )

        for (name, year), rows in seen_identity.items():
            if len(rows) > 1 and len({r.employee_id for r in rows}) > 1:
                ids = ", ".join(sorted({r.employee_id for r in rows}))
                for r in rows:
                    self._add(
                        "faculty", r, IssueSeverity.WARNING, IssueType.DUPLICATE,
                        f"Name '{r.full_name}' matches multiple employee IDs in {year}: {ids} — possible duplicate entry.",
                        field="full_name", identifier=r.employee_id,
                    )

    # -- Students ----------------------------------------------------------

    def _check_students(self, students: list[Student], program_by_id: dict):
        seen_identity: dict[tuple[str, str], list] = defaultdict(list)

        for s in students:
            seen_identity[(s.enrollment_no, s.academic_year)].append(s)

            # program_id is nullable (bulk upload doesn't require it)
            if s.program_id is not None:
                program = program_by_id.get(s.program_id)
                if program is None:
                    self._add(
                        "students", s, IssueSeverity.WARNING, IssueType.ORPHAN_REFERENCE,
                        "References a program that no longer exists.",
                        field="program_id", identifier=s.enrollment_no,
                    )
                elif s.department_id is not None and program.department_id != s.department_id:
                    self._add(
                        "students", s, IssueSeverity.WARNING, IssueType.INCONSISTENT_REFERENCE,
                        f"Student's department does not match the department of program '{program.code}'.",
                        field="department_id", identifier=s.enrollment_no,
                    )
                elif s.current_year and program.duration_years and s.current_year > program.duration_years:
                    self._add(
                        "students", s, IssueSeverity.WARNING, IssueType.LOGICAL_INCONSISTENCY,
                        f"Current year ({s.current_year}) exceeds program duration ({program.duration_years} yrs).",
                        field="current_year", identifier=s.enrollment_no,
                    )

            if s.cgpa is not None and not (0 <= s.cgpa <= 10):
                self._add(
                    "students", s, IssueSeverity.ERROR, IssueType.LOGICAL_INCONSISTENCY,
                    f"CGPA value {s.cgpa} is outside the valid 0-10 range.",
                    field="cgpa", identifier=s.enrollment_no,
                )
            if s.backlogs < 0:
                self._add(
                    "students", s, IssueSeverity.ERROR, IssueType.LOGICAL_INCONSISTENCY,
                    "Backlog count is negative.",
                    field="backlogs", identifier=s.enrollment_no,
                )
            if not s.email and not s.phone:
                self._add(
                    "students", s, IssueSeverity.WARNING, IssueType.MISSING_REQUIRED_FIELD,
                    "No email or phone on record.",
                    field="email", identifier=s.enrollment_no,
                )

        for (enrollment_no, year), rows in seen_identity.items():
            names = {r.full_name.strip().lower() for r in rows}
            if len(rows) > 1 and len(names) > 1:
                for r in rows:
                    self._add(
                        "students", r, IssueSeverity.ERROR, IssueType.DUPLICATE,
                        f"Enrollment number '{enrollment_no}' in {year} has conflicting names on file.",
                        field="full_name", identifier=enrollment_no,
                    )

    # -- Programs ------------------------------------------------------------

    def _check_programs(self, programs: list[Program]):
        for p in programs:
            if p.intake_actual > p.intake_sanctioned:
                self._add(
                    "programs", p, IssueSeverity.WARNING, IssueType.LOGICAL_INCONSISTENCY,
                    f"Actual intake ({p.intake_actual}) exceeds sanctioned intake ({p.intake_sanctioned}).",
                    field="intake_actual", identifier=p.code,
                )
            if p.is_nba_accredited and p.nba_valid_until:
                from datetime import date
                if p.nba_valid_until < date.today():
                    self._add(
                        "programs", p, IssueSeverity.WARNING, IssueType.LOGICAL_INCONSISTENCY,
                        f"NBA accreditation marked active but expired on {p.nba_valid_until}.",
                        field="nba_valid_until", identifier=p.code,
                    )

    # -- Placements / higher studies ------------------------------------------

    def _check_placements(self, placements: list[Placement], program_by_id: dict):
        for pl in placements:
            if pl.program_id and pl.program_id not in program_by_id:
                self._add(
                    "placements", pl, IssueSeverity.ERROR, IssueType.ORPHAN_REFERENCE,
                    "References a program that no longer exists.",
                    field="program_id", identifier=pl.enrollment_no or pl.student_name,
                )
            if pl.package_lpa is not None and pl.package_lpa <= 0:
                self._add(
                    "placements", pl, IssueSeverity.WARNING, IssueType.LOGICAL_INCONSISTENCY,
                    "Package (LPA) is zero or negative for a recorded placement.",
                    field="package_lpa", identifier=pl.enrollment_no or pl.student_name,
                )
            if not pl.company_name:
                self._add(
                    "placements", pl, IssueSeverity.WARNING, IssueType.MISSING_REQUIRED_FIELD,
                    "Company name is missing.",
                    field="company_name", identifier=pl.enrollment_no or pl.student_name,
                )

    # -- Research: publications / patents / funded projects -------------------

    def _check_research(self, publications, patents, projects):
        for pub in publications:
            if not pub.doi and not pub.isbn_issn:
                self._add(
                    "research_publications", pub, IssueSeverity.WARNING, IssueType.MISSING_REQUIRED_FIELD,
                    "Neither DOI nor ISBN/ISSN is recorded — needed to verify the publication.",
                    field="doi", identifier=pub.title[:60],
                )
            if pub.publication_year and pub.publication_year > 2100:
                self._add(
                    "research_publications", pub, IssueSeverity.ERROR, IssueType.LOGICAL_INCONSISTENCY,
                    f"Publication year {pub.publication_year} looks invalid.",
                    field="publication_year", identifier=pub.title[:60],
                )

        seen_patent_apps: dict[str, list] = defaultdict(list)
        for pat in patents:
            seen_patent_apps[pat.application_number].append(pat)
            if pat.grant_date and pat.filing_date and pat.grant_date < pat.filing_date:
                self._add(
                    "patents", pat, IssueSeverity.ERROR, IssueType.INVALID_DATE_RANGE,
                    "Grant date is before filing date.",
                    field="grant_date", identifier=pat.application_number,
                )
        for app_no, rows in seen_patent_apps.items():
            if len(rows) > 1:
                for r in rows:
                    self._add(
                        "patents", r, IssueSeverity.ERROR, IssueType.DUPLICATE,
                        f"Application number '{app_no}' appears on {len(rows)} patent records.",
                        field="application_number", identifier=app_no,
                    )

        for proj in projects:
            if proj.amount_received > proj.amount_sanctioned:
                self._add(
                    "funded_projects", proj, IssueSeverity.WARNING, IssueType.LOGICAL_INCONSISTENCY,
                    "Amount received exceeds amount sanctioned.",
                    field="amount_received", identifier=proj.title[:60],
                )
            if proj.start_date and proj.end_date and proj.end_date < proj.start_date:
                self._add(
                    "funded_projects", proj, IssueSeverity.ERROR, IssueType.INVALID_DATE_RANGE,
                    "End date is before start date.",
                    field="end_date", identifier=proj.title[:60],
                )
