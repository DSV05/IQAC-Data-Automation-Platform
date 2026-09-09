"""Global Search endpoint — searches across all master data categories."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import String, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user, get_db
from app.models.awards import Award
from app.models.faculty import Faculty
from app.models.green import (
    EnergyConsumption,
    GreenInitiative,
    WasteManagement,
    WaterConsumption,
)
from app.models.institutional import (
    Event,
    MoU,
)
from app.models.placement import HigherStudy, Placement
from app.models.research import (
    FundedProject,
    Patent,
    ResearchPublication,
)
from app.models.student import Student
from app.models.awards import SDGActivity

router = APIRouter()

# ── helpers ───────────────────────────────────────────────────────────────────

def _like(q: str) -> str:
    return f"%{q.lower()}%"


def _hit(category: str, record_id: str, label: str, sub: str | None,
         year: str | None, dept: str | None, extra: dict[str, Any] | None = None) -> dict:
    return {
        "category": category,
        "id": record_id,
        "label": label,
        "sublabel": sub,
        "academic_year": year,
        "department_id": str(dept) if dept else None,
        **(extra or {}),
    }


# ── route ─────────────────────────────────────────────────────────────────────

@router.get("/", summary="Global search across all master data")
async def global_search(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    categories: list[str] = Query(
        default=[
            "faculty", "students", "research", "patents",
            "placements", "mous", "events", "awards",
            "sdg", "energy", "water", "waste",
            "funded_projects", "higher_studies", "consultancy",
        ],
        description="Categories to include",
    ),
    academic_year: str | None = Query(None, description="Filter by academic year"),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: Any = Depends(get_current_user),
) -> dict:
    """
    Search across all master data categories simultaneously.
    Returns a map of category → list[hit] plus a flat `results` list
    sorted by category, limited to `limit` total entries.
    """
    like = _like(q)
    results: list[dict] = []
    category_counts: dict[str, int] = {}

    # ── Faculty ──────────────────────────────────────────────────────────────
    if "faculty" in categories:
        stmt = select(Faculty).where(
            or_(
                func.lower(Faculty.full_name).like(like),
                func.lower(Faculty.employee_id).like(like),
                func.lower(Faculty.email).like(like),
                func.lower(Faculty.designation.cast(String)).like(like),
                func.lower(Faculty.specialization).like(like),
            )
        )
        if academic_year:
            stmt = stmt.where(Faculty.academic_year == academic_year)
        rows = (await db.execute(stmt.limit(limit))).scalars().all()
        hits = [
            _hit(
                "faculty", str(r.id),
                r.full_name,
                f"{r.designation.value} · {r.academic_year}",
                r.academic_year,
                str(r.department_id),
                {"employee_id": r.employee_id, "email": r.email},
            )
            for r in rows
        ]
        results.extend(hits)
        category_counts["faculty"] = len(hits)

    # ── Students ─────────────────────────────────────────────────────────────
    if "students" in categories:
        stmt = select(Student).where(
            or_(
                func.lower(Student.full_name).like(like),
                func.lower(Student.enrollment_no).like(like),
                func.lower(Student.email).like(like),
            )
        )
        if academic_year:
            stmt = stmt.where(Student.academic_year == academic_year)
        rows = (await db.execute(stmt.limit(limit))).scalars().all()
        hits = [
            _hit(
                "students", str(r.id),
                r.full_name,
                f"Enrollment: {r.enrollment_no} · {r.academic_year}",
                r.academic_year,
                str(r.department_id),
                {"enrollment_no": r.enrollment_no},
            )
            for r in rows
        ]
        results.extend(hits)
        category_counts["students"] = len(hits)

    # ── Research Publications ─────────────────────────────────────────────────
    if "research" in categories:
        stmt = select(ResearchPublication).where(
            or_(
                func.lower(ResearchPublication.title).like(like),
                func.lower(ResearchPublication.authors).like(like),
                func.lower(ResearchPublication.journal_conference_name).like(like),
                func.lower(ResearchPublication.doi).like(like),
            )
        )
        if academic_year:
            stmt = stmt.where(ResearchPublication.academic_year == academic_year)
        rows = (await db.execute(stmt.limit(limit))).scalars().all()
        hits = [
            _hit(
                "research", str(r.id),
                r.title,
                f"{r.category.value} · {r.publication_year}",
                r.academic_year,
                str(r.department_id),
                {"doi": r.doi, "indexing": r.indexing.value},
            )
            for r in rows
        ]
        results.extend(hits)
        category_counts["research"] = len(hits)

    # ── Patents ───────────────────────────────────────────────────────────────
    if "patents" in categories:
        stmt = select(Patent).where(
            or_(
                func.lower(Patent.title).like(like),
                func.lower(Patent.application_number).like(like),
                func.lower(Patent.inventors).like(like),
            )
        )
        if academic_year:
            stmt = stmt.where(Patent.academic_year == academic_year)
        rows = (await db.execute(stmt.limit(limit))).scalars().all()
        hits = [
            _hit(
                "patents", str(r.id),
                r.title,
                f"App# {r.application_number} · {r.status.value}",
                r.academic_year,
                str(r.department_id),
                {"application_number": r.application_number},
            )
            for r in rows
        ]
        results.extend(hits)
        category_counts["patents"] = len(hits)

    # ── Placements ────────────────────────────────────────────────────────────
    if "placements" in categories:
        stmt = select(Placement).where(
            or_(
                func.lower(Placement.student_name).like(like),
                func.lower(Placement.company_name).like(like),
                func.lower(Placement.designation).like(like),
            )
        )
        if academic_year:
            stmt = stmt.where(Placement.academic_year == academic_year)
        rows = (await db.execute(stmt.limit(limit))).scalars().all()
        hits = [
            _hit(
                "placements", str(r.id),
                r.student_name,
                f"{r.company_name} · {r.designation or '—'}",
                r.academic_year,
                str(r.department_id),
                {"company_name": r.company_name, "package_lpa": r.package_lpa},
            )
            for r in rows
        ]
        results.extend(hits)
        category_counts["placements"] = len(hits)

    # ── MoUs ──────────────────────────────────────────────────────────────────
    if "mous" in categories:
        stmt = select(MoU).where(
            or_(
                func.lower(MoU.partner_name).like(like),
                func.lower(MoU.partner_country).like(like),
                func.lower(MoU.purpose).like(like),
            )
        )
        rows = (await db.execute(stmt.limit(limit))).scalars().all()
        hits = [
            _hit(
                "mous", str(r.id),
                r.partner_name,
                f"{r.partner_country} · {r.mou_type.value}",
                str(r.start_date.year) if r.start_date else None,
                None,
                {"partner_country": r.partner_country},
            )
            for r in rows
        ]
        results.extend(hits)
        category_counts["mous"] = len(hits)

    # ── Events ────────────────────────────────────────────────────────────────
    if "events" in categories:
        stmt = select(Event).where(
            or_(
                func.lower(Event.title).like(like),
                func.lower(Event.venue).like(like),
            )
        )
        if academic_year:
            stmt = stmt.where(Event.academic_year == academic_year)
        rows = (await db.execute(stmt.limit(limit))).scalars().all()
        hits = [
            _hit(
                "events", str(r.id),
                r.title,
                f"{r.event_type.value} · {r.start_date}",
                r.academic_year,
                None,
                {"event_type": r.event_type.value},
            )
            for r in rows
        ]
        results.extend(hits)
        category_counts["events"] = len(hits)

    # ── Awards ────────────────────────────────────────────────────────────────
    if "awards" in categories:
        stmt = select(Award).where(
        or_(
            func.lower(Award.title).like(like),
            func.lower(Award.awarding_body).like(like),
            func.lower(Award.recipient_name).like(like),
        )
    )

    if academic_year:
        stmt = stmt.where(Award.academic_year == academic_year)

    rows = (await db.execute(stmt.limit(limit))).scalars().all()

    hits = [
        _hit(
            "awards",
            str(r.id),
            r.title,
            f"{r.awarding_body} · {r.recipient_name}",
            r.academic_year,
            str(r.department_id) if r.department_id else None,
            {
                "awarding_body": r.awarding_body,
                "recipient_name": r.recipient_name,
                "recipient_type": r.recipient_type,
            },
        )
        for r in rows
    ]

    results.extend(hits)
    category_counts["awards"] = len(hits)

    # ── SDG Activities ────────────────────────────────────────────────────────
    if "sdg" in categories:
     stmt = select(SDGActivity).where(
        or_(
            func.lower(SDGActivity.title).like(like),
            func.lower(SDGActivity.description).like(like),
            func.lower(SDGActivity.activity_type).like(like),
            func.cast(SDGActivity.sdg_primary, String).like(like),
            func.lower(SDGActivity.sdg_secondary).like(like),
            func.lower(SDGActivity.outcome).like(like),
        )
    )

    if academic_year:
        stmt = stmt.where(SDGActivity.academic_year == academic_year)

    rows = (await db.execute(stmt.limit(limit))).scalars().all()

    hits = [
        _hit(
            "sdg",
            str(r.id),
            r.title,
            f"SDG {r.sdg_primary} · {r.activity_type}",
            r.academic_year,
            str(r.department_id) if r.department_id else None,
            {
                "sdg_goal": r.sdg_primary,
                "activity_type": r.activity_type,
            },
        )
        for r in rows
    ]

    results.extend(hits)
    category_counts["sdg"] = len(hits)

    # ── Funded Projects ───────────────────────────────────────────────────────
    if "funded_projects" in categories:
        stmt = select(FundedProject).where(
            or_(
                func.lower(FundedProject.title).like(like),
                 func.lower(FundedProject.principal_investigator).like(like),
                 func.lower(FundedProject.co_investigators).like(like),
                 func.lower(FundedProject.funding_agency_name).like(like),
                 func.lower(FundedProject.scheme).like(like),
            )
        )
        if academic_year:
            stmt = stmt.where(FundedProject.academic_year == academic_year)
        rows = (await db.execute(stmt.limit(limit))).scalars().all()
        hits = [
            _hit(
                "funded_projects", str(r.id),
                r.title,
                f"PI: {r.principal_investigator} · {r.funding_agency}",
                r.academic_year,
                str(r.department_id),
                {"funding_agency": r.funding_agency},
            )
            for r in rows
        ]
        results.extend(hits)
        category_counts["funded_projects"] = len(hits)

    # ── Higher Studies ────────────────────────────────────────────────────────
    if "higher_studies" in categories:
         stmt = select(HigherStudy).where(
        or_(
            func.lower(HigherStudy.student_name).like(like),
            func.lower(HigherStudy.enrollment_no).like(like),
            func.lower(HigherStudy.admitted_program).like(like),
            func.lower(HigherStudy.admitted_institute).like(like),
            func.lower(HigherStudy.admitted_university).like(like),
            func.lower(HigherStudy.country).like(like),
            func.lower(HigherStudy.entrance_exam).like(like),
        )
    )

    if academic_year:
        stmt = stmt.where(HigherStudy.academic_year == academic_year)

    rows = (await db.execute(stmt.limit(limit))).scalars().all()

    # ── compile ───────────────────────────────────────────────────────────────
    total = len(results)
    results = results[:limit]

    # group by category for easy frontend rendering
    by_category: dict[str, list[dict]] = {}
    for hit in results:
        by_category.setdefault(hit["category"], []).append(hit)

    return {
        "query": q,
        "total": total,
        "returned": len(results),
        "category_counts": category_counts,
        "results": results,
        "by_category": by_category,
    }
