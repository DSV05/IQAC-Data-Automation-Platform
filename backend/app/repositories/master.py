"""Master data repositories — typed wrappers over BaseRepository."""
import uuid

from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.faculty import Faculty
from app.models.student import Program, Student
from app.models.research import FundedProject, Patent, ResearchPublication
from app.models.placement import HigherStudy, Placement
from app.models.institutional import Budget, Event, Infrastructure, MoU
from app.models.green import EnergyConsumption, GreenInitiative, WasteManagement, WaterConsumption
from app.models.awards import Accreditation, Award, Consultancy, SDGActivity

# Maps a free-text month search ("Sep", "September", "9") to its 1-12 int,
# used by entities (Energy/Water/Waste) whose only "date" column is an
# integer month rather than a text field.
_MONTH_NAME_TO_NUM = {
    name.lower(): i
    for i, names in enumerate(
        [
            ("jan", "january"), ("feb", "february"), ("mar", "march"),
            ("apr", "april"), ("may",), ("jun", "june"),
            ("jul", "july"), ("aug", "august"), ("sep", "sept", "september"),
            ("oct", "october"), ("nov", "november"), ("dec", "december"),
        ],
        start=1,
    )
    for name in names
}


def _search_month(search: str) -> int | None:
    """Resolve a free-text month search term to 1-12, or None if it isn't one."""
    s = search.strip().lower()
    if s.isdigit() and 1 <= int(s) <= 12:
        return int(s)
    return _MONTH_NAME_TO_NUM.get(s)


# ── Faculty ───────────────────────────────────────────────────────────────────

class FacultyRepository(BaseRepository[Faculty]):
    model = Faculty

    async def list_by_year(
        self,
        academic_year: str,
        department_id: uuid.UUID | None = None,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
    ) -> tuple[list[Faculty], int]:
        filters = [Faculty.academic_year == academic_year]
        if department_id:
            filters.append(Faculty.department_id == department_id)
        if search:
            p = f"%{search}%"
            filters.append(
                or_(Faculty.full_name.ilike(p), Faculty.employee_id.ilike(p), Faculty.email.ilike(p))
            )
        return await self.list(page=page, size=size, filters=filters)

    async def get_by_employee_year(self, employee_id: str, academic_year: str) -> Faculty | None:
        from sqlalchemy import select
        result = await self.db.execute(
            select(Faculty).where(
                Faculty.employee_id == employee_id,
                Faculty.academic_year == academic_year,
            )
        )
        return result.scalar_one_or_none()

    async def count_by_year(self, academic_year: str) -> dict:
        """Summary counts used by dashboard."""
        from sqlalchemy import select, func
        from app.models.enums import Gender
        rows = await self.db.execute(
            select(Faculty.gender, func.count().label("cnt"))
            .where(Faculty.academic_year == academic_year, Faculty.is_active == True)
            .group_by(Faculty.gender)
        )
        result = {r.gender.value: r.cnt for r in rows}
        return {
            "total": sum(result.values()),
            "male": result.get("male", 0),
            "female": result.get("female", 0),
            "other": result.get("other", 0),
        }


# ── Programs ──────────────────────────────────────────────────────────────────

class ProgramRepository(BaseRepository[Program]):
    model = Program

    async def list_by_year(
        self,
        academic_year: str,
        department_id: uuid.UUID | None = None,
    ) -> tuple[list[Program], int]:
        filters = [Program.academic_year == academic_year]
        if department_id:
            filters.append(Program.department_id == department_id)
        return await self.list(filters=filters, size=100)


# ── Students ──────────────────────────────────────────────────────────────────

class StudentRepository(BaseRepository[Student]):
    model = Student

    async def list_by_year(
        self,
        academic_year: str,
        department_id: uuid.UUID | None = None,
        program_id: uuid.UUID | None = None,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
    ) -> tuple[list[Student], int]:
        filters = [Student.academic_year == academic_year]
        if department_id:
            filters.append(Student.department_id == department_id)
        if program_id:
            filters.append(Student.program_id == program_id)
        if search:
            p = f"%{search}%"
            filters.append(
                or_(Student.full_name.ilike(p), Student.enrollment_no.ilike(p))
            )
        return await self.list(page=page, size=size, filters=filters)

    async def get_by_enrollment_year(self, enrollment_no: str, academic_year: str) -> Student | None:
        from sqlalchemy import select
        result = await self.db.execute(
            select(Student).where(
                Student.enrollment_no == enrollment_no,
                Student.academic_year == academic_year,
            )
        )
        return result.scalar_one_or_none()

    async def count_by_year(self, academic_year: str) -> dict:
        from sqlalchemy import select, func
        from app.models.enums import Gender
        rows = await self.db.execute(
            select(Student.gender, func.count().label("cnt"))
            .where(Student.academic_year == academic_year, Student.is_active == True)
            .group_by(Student.gender)
        )
        result = {r.gender.value: r.cnt for r in rows}
        return {
            "total": sum(result.values()),
            "male": result.get("male", 0),
            "female": result.get("female", 0),
            "other": result.get("other", 0),
        }


# ── Research Publications ─────────────────────────────────────────────────────

class ResearchRepository(BaseRepository[ResearchPublication]):
    model = ResearchPublication

    async def list_by_year(
        self,
        academic_year: str,
        department_id: uuid.UUID | None = None,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
    ) -> tuple[list[ResearchPublication], int]:
        filters = [ResearchPublication.academic_year == academic_year]
        if department_id:
            filters.append(ResearchPublication.department_id == department_id)
        if search:
            p = f"%{search}%"
            filters.append(
                or_(
                    ResearchPublication.title.ilike(p),
                    ResearchPublication.authors.ilike(p),
                    ResearchPublication.doi.ilike(p),
                )
            )
        return await self.list(page=page, size=size, filters=filters)


class PatentRepository(BaseRepository[Patent]):
    model = Patent

    async def list_by_year(
        self, academic_year: str, department_id: uuid.UUID | None = None,
        page: int = 1, size: int = 20, search: str | None = None,
    ) -> tuple[list[Patent], int]:
        filters = [Patent.academic_year == academic_year]
        if department_id:
            filters.append(Patent.department_id == department_id)
        if search:
            p = f"%{search}%"
            filters.append(
                or_(
                    Patent.title.ilike(p),
                    Patent.inventors.ilike(p),
                    Patent.application_number.ilike(p),
                )
            )
        return await self.list(page=page, size=size, filters=filters)


class ProjectRepository(BaseRepository[FundedProject]):
    model = FundedProject

    async def list_by_year(
        self, academic_year: str, department_id: uuid.UUID | None = None,
        page: int = 1, size: int = 20,
    ) -> tuple[list[FundedProject], int]:
        filters = [FundedProject.academic_year == academic_year]
        if department_id:
            filters.append(FundedProject.department_id == department_id)
        return await self.list(page=page, size=size, filters=filters)


# ── Placements ────────────────────────────────────────────────────────────────

class PlacementRepository(BaseRepository[Placement]):
    model = Placement

    async def list_by_year(
        self, academic_year: str, department_id: uuid.UUID | None = None,
        page: int = 1, size: int = 20, search: str | None = None,
    ) -> tuple[list[Placement], int]:
        filters = [Placement.academic_year == academic_year]
        if department_id:
            filters.append(Placement.department_id == department_id)
        if search:
            p = f"%{search}%"
            filters.append(
                or_(Placement.student_name.ilike(p), Placement.company_name.ilike(p))
            )
        return await self.list(page=page, size=size, filters=filters)

    async def stats_by_year(self, academic_year: str) -> dict:
        from sqlalchemy import select, func
        rows = await self.db.execute(
            select(
                func.count().label("total"),
                func.avg(Placement.package_lpa).label("avg_package"),
                func.max(Placement.package_lpa).label("max_package"),
            ).where(Placement.academic_year == academic_year)
        )
        r = rows.one()
        return {
            "total_placed": r.total or 0,
            "avg_package_lpa": round(r.avg_package or 0, 2),
            "max_package_lpa": round(r.max_package or 0, 2),
        }


class HigherStudyRepository(BaseRepository[HigherStudy]):
    model = HigherStudy

    async def list_by_year(
        self, academic_year: str, department_id: uuid.UUID | None = None,
        page: int = 1, size: int = 20,
    ) -> tuple[list[HigherStudy], int]:
        filters = [HigherStudy.academic_year == academic_year]
        if department_id:
            filters.append(HigherStudy.department_id == department_id)
        return await self.list(page=page, size=size, filters=filters)


# ── Institutional ─────────────────────────────────────────────────────────────

class InfrastructureRepository(BaseRepository[Infrastructure]):
    model = Infrastructure

    async def list_by_year(
        self, academic_year: str, department_id: uuid.UUID | None = None,
        page: int = 1, size: int = 50,
    ) -> tuple[list[Infrastructure], int]:
        filters = [Infrastructure.academic_year == academic_year]
        if department_id:
            filters.append(Infrastructure.department_id == department_id)
        return await self.list(page=page, size=size, filters=filters)


class BudgetRepository(BaseRepository[Budget]):
    model = Budget

    async def list_by_year(
        self, academic_year: str, department_id: uuid.UUID | None = None,
        page: int = 1, size: int = 100,
    ) -> tuple[list[Budget], int]:
        filters = [Budget.academic_year == academic_year]
        if department_id:
            filters.append(Budget.department_id == department_id)
        return await self.list(page=page, size=size, filters=filters)

    async def totals_by_year(self, academic_year: str) -> dict:
        from sqlalchemy import select, func
        rows = await self.db.execute(
            select(
                Budget.category,
                func.sum(Budget.amount_actual).label("total"),
            )
            .where(Budget.academic_year == academic_year)
            .group_by(Budget.category)
        )
        return {r.category: r.total or 0 for r in rows}


class MoURepository(BaseRepository[MoU]):
    model = MoU

    async def list_by_year(
        self, academic_year: str, department_id: uuid.UUID | None = None,
        page: int = 1, size: int = 20, search: str | None = None,
    ) -> tuple[list[MoU], int]:
        filters = [MoU.academic_year == academic_year]
        if department_id:
            filters.append(MoU.department_id == department_id)
        if search:
            p = f"%{search}%"
            filters.append(
                or_(
                    MoU.partner_name.ilike(p),
                    MoU.partner_country.ilike(p),
                    MoU.purpose.ilike(p),
                )
            )
        return await self.list(page=page, size=size, filters=filters)


class EventRepository(BaseRepository[Event]):
    model = Event

    async def list_by_year(
        self, academic_year: str, department_id: uuid.UUID | None = None,
        page: int = 1, size: int = 20, search: str | None = None,
    ) -> tuple[list[Event], int]:
        filters = [Event.academic_year == academic_year]
        if department_id:
            filters.append(Event.department_id == department_id)
        if search:
            p = f"%{search}%"
            filters.append(
                or_(Event.title.ilike(p), Event.venue.ilike(p))
            )
        return await self.list(page=page, size=size, filters=filters)


# ── Green ─────────────────────────────────────────────────────────────────────

class EnergyRepository(BaseRepository[EnergyConsumption]):
    model = EnergyConsumption

    async def list_by_year(
        self, academic_year: str, page: int = 1, size: int = 50,
        search: str | None = None,
    ) -> tuple[list[EnergyConsumption], int]:
        filters = [EnergyConsumption.academic_year == academic_year]
        if search:
            month_num = _search_month(search)
            if month_num is not None:
                filters.append(EnergyConsumption.month == month_num)
            else:
                # No text columns to search on Energy — a non-month term matches nothing.
                filters.append(EnergyConsumption.id == None)  # noqa: E711
        return await self.list(page=page, size=size, filters=filters)

    async def totals_by_year(self, academic_year: str) -> dict:
        from sqlalchemy import select, func
        r = (await self.db.execute(
            select(
                func.sum(EnergyConsumption.electricity_kwh).label("grid"),
                func.sum(EnergyConsumption.solar_kwh).label("solar"),
                func.sum(EnergyConsumption.wind_kwh).label("wind"),
                func.sum(EnergyConsumption.diesel_liters).label("diesel"),
                func.sum(EnergyConsumption.ghg_scope1_tco2e).label("scope1"),
                func.sum(EnergyConsumption.ghg_scope2_tco2e).label("scope2"),
            ).where(EnergyConsumption.academic_year == academic_year)
        )).one()
        return {
            "electricity_kwh": r.grid or 0,
            "solar_kwh": r.solar or 0,
            "wind_kwh": r.wind or 0,
            "diesel_liters": r.diesel or 0,
            "ghg_scope1_tco2e": r.scope1 or 0,
            "ghg_scope2_tco2e": r.scope2 or 0,
            "renewable_pct": round(
                ((r.solar or 0) + (r.wind or 0)) / max((r.grid or 1), 1) * 100, 1
            ),
        }


class WaterRepository(BaseRepository[WaterConsumption]):
    model = WaterConsumption

    async def list_by_year(
        self, academic_year: str, page: int = 1, size: int = 50,
        search: str | None = None,
    ) -> tuple[list[WaterConsumption], int]:
        filters = [WaterConsumption.academic_year == academic_year]
        if search:
            month_num = _search_month(search)
            if month_num is not None:
                filters.append(WaterConsumption.month == month_num)
            else:
                filters.append(WaterConsumption.remarks.ilike(f"%{search}%"))
        return await self.list(page=page, size=size, filters=filters)


class WasteRepository(BaseRepository[WasteManagement]):
    model = WasteManagement

    async def list_by_year(
        self, academic_year: str, page: int = 1, size: int = 50,
        search: str | None = None,
    ) -> tuple[list[WasteManagement], int]:
        filters = [WasteManagement.academic_year == academic_year]
        if search:
            month_num = _search_month(search)
            if month_num is not None:
                filters.append(WasteManagement.month == month_num)
            else:
                p = f"%{search}%"
                filters.append(
                    or_(
                        WasteManagement.waste_type.ilike(p),
                        WasteManagement.disposal_method.ilike(p),
                        WasteManagement.vendor_name.ilike(p),
                    )
                )
        return await self.list(page=page, size=size, filters=filters)


class GreenInitiativeRepository(BaseRepository[GreenInitiative]):
    model = GreenInitiative

    async def list_by_year(
        self, academic_year: str, page: int = 1, size: int = 50,
    ) -> tuple[list[GreenInitiative], int]:
        return await self.list(
            page=page, size=size,
            filters=[GreenInitiative.academic_year == academic_year],
        )


# ── Awards / Accreditations ───────────────────────────────────────────────────

class AwardRepository(BaseRepository[Award]):
    model = Award

    async def list_by_year(
        self, academic_year: str, department_id: uuid.UUID | None = None,
        page: int = 1, size: int = 20, search: str | None = None,
    ) -> tuple[list[Award], int]:
        filters = [Award.academic_year == academic_year]
        if department_id:
            filters.append(Award.department_id == department_id)
        if search:
            p = f"%{search}%"
            filters.append(
                or_(
                    Award.recipient_name.ilike(p),
                    Award.title.ilike(p),
                    Award.awarding_body.ilike(p),
                )
            )
        return await self.list(page=page, size=size, filters=filters)


class AccreditationRepository(BaseRepository[Accreditation]):
    model = Accreditation

    async def list_active(self) -> list[Accreditation]:
        items, _ = await self.list(
            size=100, filters=[Accreditation.is_active == True]
        )
        return items


class ConsultancyRepository(BaseRepository[Consultancy]):
    model = Consultancy

    async def list_by_year(
        self, academic_year: str, department_id: uuid.UUID | None = None,
        page: int = 1, size: int = 20,
    ) -> tuple[list[Consultancy], int]:
        filters = [Consultancy.academic_year == academic_year]
        if department_id:
            filters.append(Consultancy.department_id == department_id)
        return await self.list(page=page, size=size, filters=filters)


class SDGRepository(BaseRepository[SDGActivity]):
    model = SDGActivity

    async def list_by_year(
        self, academic_year: str, sdg_goal: int | None = None,
        page: int = 1, size: int = 20, search: str | None = None,
    ) -> tuple[list[SDGActivity], int]:
        filters = [SDGActivity.academic_year == academic_year]
        if sdg_goal:
            filters.append(SDGActivity.sdg_primary == sdg_goal)
        if search:
            p = f"%{search}%"
            filters.append(
                or_(
                    SDGActivity.title.ilike(p),
                    SDGActivity.description.ilike(p),
                    SDGActivity.outcome.ilike(p),
                )
            )
        return await self.list(page=page, size=size, filters=filters)
