"""
Module 8 — Report Generator
=============================
Pulls and aggregates data from the master tables for each report type.
Kept separate from the file-formatting code so the same numbers feed
both the Excel and PDF renderers without duplicating any queries.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.awards import Accreditation, Award, Consultancy, SDGActivity
from app.models.faculty import Faculty
from app.models.green import GreenInitiative
from app.models.institutional import Budget, Event, Infrastructure, MoU
from app.models.research import FundedProject, Patent, ResearchPublication
from app.models.placement import HigherStudy, Placement
from app.models.student import Program, Student
from app.models.user import Department


def _year_filter(model, academic_year: str | None):
    return model.academic_year == academic_year if academic_year else True


async def get_nirf_data(db: AsyncSession, academic_year: str | None) -> dict:
    """NIRF cares about: faculty ratios, research output & citations, placements, patents."""
    faculty_total = await db.scalar(
        select(func.count()).select_from(Faculty).where(
            Faculty.is_active == True, _year_filter(Faculty, academic_year)  # noqa: E712
        )
    )
    faculty_phd = await db.scalar(
        select(func.count()).select_from(Faculty).where(
            Faculty.is_active == True, Faculty.phd_awarded == True,  # noqa: E712
            _year_filter(Faculty, academic_year),
        )
    )
    student_total = await db.scalar(
        select(func.count()).select_from(Student).where(
            Student.is_active == True, _year_filter(Student, academic_year)  # noqa: E712
        )
    )

    pub_stats = (await db.execute(
        select(
            func.count(ResearchPublication.id),
            func.coalesce(func.sum(ResearchPublication.citations), 0),
        ).where(_year_filter(ResearchPublication, academic_year))
    )).first()

    patents_filed = await db.scalar(
        select(func.count()).select_from(Patent).where(_year_filter(Patent, academic_year))
    )
    patents_granted = await db.scalar(
        select(func.count()).select_from(Patent).where(
            Patent.status == "granted", _year_filter(Patent, academic_year)
        )
    )

    funded_stats = (await db.execute(
        select(
            func.count(FundedProject.id),
            func.coalesce(func.sum(FundedProject.amount_received), 0.0),
        ).where(_year_filter(FundedProject, academic_year))
    )).first()

    placement_stats = (await db.execute(
        select(
            func.count(Placement.id),
            func.coalesce(func.avg(Placement.package_lpa), 0.0),
            func.coalesce(func.max(Placement.package_lpa), 0.0),
        ).where(_year_filter(Placement, academic_year))
    )).first()

    higher_studies_total = await db.scalar(
        select(func.count()).select_from(HigherStudy).where(_year_filter(HigherStudy, academic_year))
    )

    dept_rows = (await db.execute(
        select(Department.name, func.count(Faculty.id))
        .join(Faculty, Faculty.department_id == Department.id)
        .where(Faculty.is_active == True, _year_filter(Faculty, academic_year))  # noqa: E712
        .group_by(Department.name)
        .order_by(Department.name)
    )).all()

    return {
        "academic_year": academic_year or "All years",
        "faculty_total": faculty_total or 0,
        "faculty_phd": faculty_phd or 0,
        "faculty_phd_pct": round((faculty_phd or 0) / faculty_total * 100, 1) if faculty_total else 0,
        "student_total": student_total or 0,
        "faculty_student_ratio": round(student_total / faculty_total, 2) if faculty_total else None,
        "publications_count": pub_stats[0] or 0,
        "publications_citations": pub_stats[1] or 0,
        "patents_filed": patents_filed or 0,
        "patents_granted": patents_granted or 0,
        "funded_projects_count": funded_stats[0] or 0,
        "funded_projects_amount": float(funded_stats[1] or 0),
        "placements_count": placement_stats[0] or 0,
        "placements_avg_package_lpa": round(float(placement_stats[1] or 0), 2),
        "placements_max_package_lpa": round(float(placement_stats[2] or 0), 2),
        "higher_studies_count": higher_studies_total or 0,
        "faculty_by_department": [{"department": d, "count": c} for d, c in dept_rows],
    }


async def get_naac_data(db: AsyncSession, academic_year: str | None) -> dict:
    """NAAC SSR is organized by criteria; we map available tables to the closest criterion."""
    # Criterion I — Curricular Aspects
    programs_total = await db.scalar(
        select(func.count()).select_from(Program).where(_year_filter(Program, academic_year))
    )
    nba_accredited = await db.scalar(
        select(func.count()).select_from(Program).where(
            Program.is_nba_accredited == True, _year_filter(Program, academic_year)  # noqa: E712
        )
    )

    # Criterion II — Teaching-Learning and Evaluation
    faculty_total = await db.scalar(select(func.count()).select_from(Faculty).where(Faculty.is_active == True))  # noqa: E712
    student_total = await db.scalar(select(func.count()).select_from(Student).where(Student.is_active == True))  # noqa: E712

    # Criterion III — Research, Innovations and Extension
    pub_count = await db.scalar(
        select(func.count()).select_from(ResearchPublication).where(_year_filter(ResearchPublication, academic_year))
    )
    consultancy_stats = (await db.execute(
        select(func.count(Consultancy.id), func.coalesce(func.sum(Consultancy.amount_inr), 0.0))
        .where(_year_filter(Consultancy, academic_year))
    )).first()
    sdg_activities = await db.scalar(
        select(func.count()).select_from(SDGActivity).where(_year_filter(SDGActivity, academic_year))
    )
    extension_events = await db.scalar(
        select(func.count()).select_from(Event).where(_year_filter(Event, academic_year))
    )

    # Criterion IV — Infrastructure and Learning Resources
    infra_rows = (await db.execute(
        select(Infrastructure.facility_type, func.coalesce(func.sum(Infrastructure.count), 0))
        .where(_year_filter(Infrastructure, academic_year))
        .group_by(Infrastructure.facility_type)
    )).all()

    # Criterion V — Student Support and Progression
    placements_count = await db.scalar(
        select(func.count()).select_from(Placement).where(_year_filter(Placement, academic_year))
    )
    higher_studies_count = await db.scalar(
        select(func.count()).select_from(HigherStudy).where(_year_filter(HigherStudy, academic_year))
    )

    # Criterion VI — Governance, Leadership and Management
    budget_stats = (await db.execute(
        select(
            func.coalesce(func.sum(Budget.amount_budgeted), 0.0),
            func.coalesce(func.sum(Budget.amount_actual), 0.0),
        ).where(_year_filter(Budget, academic_year))
    )).first()
    mous_active = await db.scalar(
        select(func.count()).select_from(MoU).where(MoU.is_active == True, _year_filter(MoU, academic_year))  # noqa: E712
    )

    # Criterion VII — Institutional Values and Best Practices
    green_initiatives_count = await db.scalar(
        select(func.count()).select_from(GreenInitiative).where(_year_filter(GreenInitiative, academic_year))
    )
    awards_count = await db.scalar(
        select(func.count()).select_from(Award).where(_year_filter(Award, academic_year))
    )

    accreditations = (await db.execute(
        select(Accreditation.name, Accreditation.grade_score, Accreditation.valid_until)
        .where(Accreditation.is_active == True)  # noqa: E712
    )).all()

    return {
        "academic_year": academic_year or "All years",
        "criterion_1_curricular": {
            "programs_total": programs_total or 0,
            "nba_accredited_programs": nba_accredited or 0,
        },
        "criterion_2_teaching_learning": {
            "faculty_total": faculty_total or 0,
            "student_total": student_total or 0,
        },
        "criterion_3_research": {
            "publications": pub_count or 0,
            "consultancy_projects": consultancy_stats[0] or 0,
            "consultancy_amount_inr": float(consultancy_stats[1] or 0),
            "sdg_activities": sdg_activities or 0,
            "extension_activities": extension_events or 0,
        },
        "criterion_4_infrastructure": [
            {"facility_type": f, "count": c} for f, c in infra_rows
        ],
        "criterion_5_student_support": {
            "placements": placements_count or 0,
            "higher_studies": higher_studies_count or 0,
        },
        "criterion_6_governance": {
            "budget_planned_inr": float(budget_stats[0] or 0),
            "budget_utilized_inr": float(budget_stats[1] or 0),
            "active_mous": mous_active or 0,
        },
        "criterion_7_institutional_values": {
            "green_initiatives": green_initiatives_count or 0,
            "awards_received": awards_count or 0,
        },
        "accreditations": [
            {"name": a, "grade": g, "valid_until": str(v) if v else None} for a, g, v in accreditations
        ],
    }


async def get_aishe_data(db: AsyncSession, academic_year: str | None) -> dict:
    """AISHE cares about institutional profile: program-wise enrollment, faculty by designation/gender."""
    program_rows = (await db.execute(
        select(Program.name, Program.level, Program.intake_sanctioned, Program.intake_actual)
        .where(_year_filter(Program, academic_year))
        .order_by(Program.name)
    )).all()

    faculty_by_designation = (await db.execute(
        select(Faculty.designation, func.count(Faculty.id))
        .where(Faculty.is_active == True, _year_filter(Faculty, academic_year))  # noqa: E712
        .group_by(Faculty.designation)
    )).all()

    faculty_by_gender = (await db.execute(
        select(Faculty.gender, func.count(Faculty.id))
        .where(Faculty.is_active == True, _year_filter(Faculty, academic_year))  # noqa: E712
        .group_by(Faculty.gender)
    )).all()

    students_by_gender = (await db.execute(
        select(Student.gender, func.count(Student.id))
        .where(Student.is_active == True, _year_filter(Student, academic_year))  # noqa: E712
        .group_by(Student.gender)
    )).all()

    students_by_category = (await db.execute(
        select(Student.category, func.count(Student.id))
        .where(Student.is_active == True, _year_filter(Student, academic_year))  # noqa: E712
        .group_by(Student.category)
    )).all()

    return {
        "academic_year": academic_year or "All years",
        "programs": [
            {
                "name": name, "level": level.value if hasattr(level, "value") else level,
                "intake_sanctioned": sanctioned, "intake_actual": actual,
            }
            for name, level, sanctioned, actual in program_rows
        ],
        "faculty_by_designation": [
            {"designation": d.value if hasattr(d, "value") else d, "count": c} for d, c in faculty_by_designation
        ],
        "faculty_by_gender": [
            {"gender": g.value if hasattr(g, "value") else g, "count": c} for g, c in faculty_by_gender
        ],
        "students_by_gender": [
            {"gender": g.value if hasattr(g, "value") else g, "count": c} for g, c in students_by_gender
        ],
        "students_by_category": [
            {"category": cat.value if hasattr(cat, "value") else cat, "count": c} for cat, c in students_by_category
        ],
    }
