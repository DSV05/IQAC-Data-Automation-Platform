"""
Module 5 — Dashboard Aggregation Service
=========================================
Single entrypoint (`DashboardService.get_summary`) that gathers everything
the dashboard page needs in one round trip: headline KPIs, department
breakdowns, year-over-year trends, and the green/SDG widgets.

Kept as raw aggregate SQL (func.count/sum/avg + group_by) rather than
pulling full rows into Python, since these are exactly the queries that
matter for accreditation dashboards and should stay cheap as data grows.
"""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.awards import SDGActivity
from app.models.faculty import Faculty
from app.models.green import EnergyConsumption
from app.models.placement import Placement
from app.models.research import FundedProject, Patent, ResearchPublication
from app.models.student import Student
from app.models.user import Department

# Last N academic years to show in year-over-year trend charts.
# Academic years are stored as "2024-25" strings, sorted lexicographically
# which happens to also be chronological for this format.
TREND_YEARS_COUNT = 5


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(self, academic_year: str) -> dict:
        kpis = await self._kpis(academic_year)
        dept_breakdown = await self._dept_breakdown(academic_year)
        yoy = await self._year_over_year()
        energy = await self._energy_widget(academic_year)
        sdg = await self._sdg_widget(academic_year)

        return {
            "academic_year": academic_year,
            "kpis": kpis,
            "dept_breakdown": dept_breakdown,
            "year_over_year": yoy,
            "energy": energy,
            "sdg": sdg,
        }

    # -- KPI cards -----------------------------------------------------------

    async def _kpis(self, academic_year: str) -> dict:
        total_faculty = await self._scalar(
            select(func.count()).select_from(Faculty)
            .where(Faculty.academic_year == academic_year, Faculty.is_active == True)  # noqa: E712
        )
        total_students = await self._scalar(
            select(func.count()).select_from(Student)
            .where(Student.academic_year == academic_year, Student.is_active == True)  # noqa: E712
        )
        placement_row = (await self.db.execute(
            select(
                func.count().label("total_recorded"),
                func.avg(Placement.package_lpa).label("avg_package"),
            ).where(Placement.academic_year == academic_year)
        )).one()
        total_publications = await self._scalar(
            select(func.count()).select_from(ResearchPublication)
            .where(ResearchPublication.academic_year == academic_year)
        )
        total_patents = await self._scalar(
            select(func.count()).select_from(Patent)
            .where(Patent.academic_year == academic_year)
        )
        funded_total = await self._scalar(
            select(func.coalesce(func.sum(FundedProject.amount_sanctioned), 0))
            .where(FundedProject.academic_year == academic_year)
        )
        total_departments = await self._scalar(
            select(func.count()).select_from(Department).where(Department.is_active == True)  # noqa: E712
        )

        placement_rate = (
            round((placement_row.total_recorded or 0) / total_students * 100, 1)
            if total_students else 0.0
        )

        return {
            "total_faculty": total_faculty,
            "total_students": total_students,
            "student_faculty_ratio": round(total_students / total_faculty, 1) if total_faculty else None,
            "total_placed": placement_row.total_recorded or 0,
            "placement_rate_pct": placement_rate,
            "avg_package_lpa": round(placement_row.avg_package or 0, 2),
            "total_publications": total_publications,
            "total_patents": total_patents,
            "total_funded_amount_inr": funded_total,
            "total_departments": total_departments,
        }

    # -- Department breakdown -------------------------------------------------

    async def _dept_breakdown(self, academic_year: str) -> dict:
        faculty_rows = await self.db.execute(
            select(Department.name, func.count(Faculty.id))
            .join(Faculty, Faculty.department_id == Department.id)
            .where(Faculty.academic_year == academic_year, Faculty.is_active == True)  # noqa: E712
            .group_by(Department.name)
            .order_by(func.count(Faculty.id).desc())
        )
        student_rows = await self.db.execute(
            select(Department.name, func.count(Student.id))
            .join(Student, Student.department_id == Department.id)
            .where(Student.academic_year == academic_year, Student.is_active == True)  # noqa: E712
            .group_by(Department.name)
            .order_by(func.count(Student.id).desc())
        )
        publication_rows = await self.db.execute(
            select(Department.name, func.count(ResearchPublication.id))
            .join(ResearchPublication, ResearchPublication.department_id == Department.id)
            .where(ResearchPublication.academic_year == academic_year)
            .group_by(Department.name)
            .order_by(func.count(ResearchPublication.id).desc())
        )

        return {
            "faculty_by_department": [{"department": n, "count": c} for n, c in faculty_rows],
            "students_by_department": [{"department": n, "count": c} for n, c in student_rows],
            "publications_by_department": [{"department": n, "count": c} for n, c in publication_rows],
        }

    # -- Year-over-year trends -------------------------------------------------

    async def _year_over_year(self) -> dict:
        async def trend(model, extra_filter=None):
            stmt = select(model.academic_year, func.count()).group_by(model.academic_year).order_by(model.academic_year)
            if extra_filter is not None:
                stmt = stmt.where(extra_filter)
            rows = await self.db.execute(stmt)
            data = [{"academic_year": y, "count": c} for y, c in rows]
            return data[-TREND_YEARS_COUNT:]

        return {
            "faculty": await trend(Faculty, Faculty.is_active == True),  # noqa: E712
            "students": await trend(Student, Student.is_active == True),  # noqa: E712
            "publications": await trend(ResearchPublication),
            "placements": await trend(Placement),
        }

    # -- Energy / green widget --------------------------------------------------

    async def _energy_widget(self, academic_year: str) -> dict:
        current = (await self.db.execute(
            select(
                func.coalesce(func.sum(EnergyConsumption.electricity_kwh), 0).label("grid"),
                func.coalesce(func.sum(EnergyConsumption.solar_kwh), 0).label("solar"),
                func.coalesce(func.sum(EnergyConsumption.wind_kwh), 0).label("wind"),
                func.coalesce(func.sum(EnergyConsumption.ghg_scope1_tco2e), 0).label("scope1"),
                func.coalesce(func.sum(EnergyConsumption.ghg_scope2_tco2e), 0).label("scope2"),
            ).where(EnergyConsumption.academic_year == academic_year)
        )).one()

        renewable = (current.solar or 0) + (current.wind or 0)
        total = renewable + (current.grid or 0)
        renewable_pct = round(renewable / total * 100, 1) if total else 0.0

        yoy_rows = await self.db.execute(
            select(
                EnergyConsumption.academic_year,
                func.sum(EnergyConsumption.ghg_scope1_tco2e + EnergyConsumption.ghg_scope2_tco2e),
            )
            .group_by(EnergyConsumption.academic_year)
            .order_by(EnergyConsumption.academic_year)
        )
        ghg_trend = [{"academic_year": y, "total_tco2e": round(v or 0, 2)} for y, v in yoy_rows][-TREND_YEARS_COUNT:]

        return {
            "electricity_kwh": current.grid or 0,
            "solar_kwh": current.solar or 0,
            "wind_kwh": current.wind or 0,
            "renewable_pct": renewable_pct,
            "ghg_scope1_tco2e": round(current.scope1 or 0, 2),
            "ghg_scope2_tco2e": round(current.scope2 or 0, 2),
            "ghg_trend": ghg_trend,
        }

    # -- SDG widget ---------------------------------------------------------

    async def _sdg_widget(self, academic_year: str) -> dict:
        rows = await self.db.execute(
            select(SDGActivity.sdg_primary, func.count())
            .where(SDGActivity.academic_year == academic_year)
            .group_by(SDGActivity.sdg_primary)
            .order_by(SDGActivity.sdg_primary)
        )
        by_goal = [{"sdg_goal": g, "count": c} for g, c in rows]
        total = sum(item["count"] for item in by_goal)
        return {"total_activities": total, "activities_by_goal": by_goal}

    # -- Helpers ---------------------------------------------------------------

    async def _scalar(self, stmt) -> int:
        result = await self.db.execute(stmt)
        return result.scalar() or 0
