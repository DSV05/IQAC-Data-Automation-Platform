"""
Master Data API Endpoints
=========================
All endpoints follow: /api/v1/master/{entity}
Each entity supports: GET list, POST create, GET {id}, PUT {id}, DELETE {id}

Academic year format: "2023-24"
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentUser
from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.user import User
from app.repositories.master import (
    AccreditationRepository, AwardRepository, BudgetRepository,
    ConsultancyRepository, EnergyRepository, EventRepository,
    FacultyRepository, GreenInitiativeRepository, HigherStudyRepository,
    InfrastructureRepository, MoURepository, PatentRepository,
    PlacementRepository, ProgramRepository, ProjectRepository,
    ResearchRepository, SDGRepository, StudentRepository,
    WasteRepository, WaterRepository,
)
from app.schemas import master as s
from app.services.master import FacultyService, make_service

router = APIRouter()


# ── Dependency helpers ────────────────────────────────────────────────────────

def get_db_session(db: AsyncSession = Depends(get_db)):
    return db


# ── Programs ──────────────────────────────────────────────────────────────────

@router.get("/programs", response_model=s.PaginatedResponse)
async def list_programs(
    academic_year: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    department_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(require_permission("faculty:read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await ProgramRepository(db).list_by_year(academic_year, department_id)
    return {"items": [s.ProgramRead.model_validate(i) for i in items], "total": total, "page": 1, "size": 100, "pages": 1}


@router.post("/programs", response_model=s.ProgramRead, status_code=201)
async def create_program(
    data: s.ProgramCreate,
    current_user: User = Depends(require_permission("faculty:create")),
    db: AsyncSession = Depends(get_db),
):
    item = await ProgramRepository(db).create(**data.model_dump())
    return s.ProgramRead.model_validate(item)


@router.put("/programs/{program_id}", response_model=s.ProgramRead)
async def update_program(
    program_id: uuid.UUID,
    data: s.ProgramUpdate,
    current_user: User = Depends(require_permission("faculty:update")),
    db: AsyncSession = Depends(get_db),
):
    repo = ProgramRepository(db)
    item = await repo.get_by_id(program_id)
    if not item:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Program not found")
    item = await repo.update(item, **data.model_dump(exclude_unset=True))
    return s.ProgramRead.model_validate(item)


# ── Faculty ───────────────────────────────────────────────────────────────────

@router.get("/faculty", response_model=s.PaginatedFaculty)
async def list_faculty(
    academic_year: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    department_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    page: int = 1,
    size: int = 20,
    current_user: User = Depends(require_permission("faculty:read")),
    db: AsyncSession = Depends(get_db),
):
    svc = FacultyService(FacultyRepository(db))
    return await svc.list(academic_year, department_id, page, size, search)


@router.post("/faculty", response_model=s.FacultyRead, status_code=201)
async def create_faculty(
    data: s.FacultyCreate,
    current_user: User = Depends(require_permission("faculty:create")),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService(FacultyRepository(db)).create(data)


@router.get("/faculty/summary", response_model=dict)
async def faculty_summary(
    academic_year: str = Query(...),
    current_user: User = Depends(require_permission("faculty:read")),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService(FacultyRepository(db)).summary(academic_year)


@router.get("/faculty/{record_id}", response_model=s.FacultyRead)
async def get_faculty(
    record_id: uuid.UUID,
    current_user: User = Depends(require_permission("faculty:read")),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService(FacultyRepository(db)).get(record_id)


@router.put("/faculty/{record_id}", response_model=s.FacultyRead)
async def update_faculty(
    record_id: uuid.UUID,
    data: s.FacultyUpdate,
    current_user: User = Depends(require_permission("faculty:update")),
    db: AsyncSession = Depends(get_db),
):
    return await FacultyService(FacultyRepository(db)).update(record_id, data)


@router.delete("/faculty/{record_id}", status_code=204)
async def delete_faculty(
    record_id: uuid.UUID,
    current_user: User = Depends(require_permission("faculty:delete")),
    db: AsyncSession = Depends(get_db),
):
    await FacultyService(FacultyRepository(db)).delete(record_id)


# ── Students ──────────────────────────────────────────────────────────────────

@router.get("/students", response_model=s.PaginatedStudents)
async def list_students(
    academic_year: str = Query(...),
    department_id: Optional[uuid.UUID] = None,
    program_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    page: int = 1, size: int = 20,
    current_user: User = Depends(require_permission("students:read")),
    db: AsyncSession = Depends(get_db),
):
    repo = StudentRepository(db)
    items, total = await repo.list_by_year(academic_year, department_id, program_id, page, size, search)
    import math
    return s.PaginatedStudents(
        items=[s.StudentRead.model_validate(i) for i in items],
        total=total, page=page, size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.post("/students", response_model=s.StudentRead, status_code=201)
async def create_student(
    data: s.StudentCreate,
    current_user: User = Depends(require_permission("students:create")),
    db: AsyncSession = Depends(get_db),
):
    item = await StudentRepository(db).create(**data.model_dump())
    return s.StudentRead.model_validate(item)


@router.get("/students/summary", response_model=dict)
async def student_summary(
    academic_year: str = Query(...),
    current_user: User = Depends(require_permission("students:read")),
    db: AsyncSession = Depends(get_db),
):
    return await StudentRepository(db).count_by_year(academic_year)


@router.get("/students/{record_id}", response_model=s.StudentRead)
async def get_student(
    record_id: uuid.UUID,
    current_user: User = Depends(require_permission("students:read")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    item = await StudentRepository(db).get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Student not found")
    return s.StudentRead.model_validate(item)


@router.put("/students/{record_id}", response_model=s.StudentRead)
async def update_student(
    record_id: uuid.UUID,
    data: s.StudentUpdate,
    current_user: User = Depends(require_permission("students:update")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = StudentRepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Student not found")
    item = await repo.update(item, **data.model_dump(exclude_unset=True))
    return s.StudentRead.model_validate(item)


@router.delete("/students/{record_id}", status_code=204)
async def delete_student(
    record_id: uuid.UUID,
    current_user: User = Depends(require_permission("students:delete")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = StudentRepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Student not found")
    await repo.delete(item)


# ── Research Publications ─────────────────────────────────────────────────────

@router.get("/research", response_model=s.PaginatedResearch)
async def list_research(
    academic_year: str = Query(...),
    department_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    page: int = 1, size: int = 20,
    current_user: User = Depends(require_permission("research:read")),
    db: AsyncSession = Depends(get_db),
):
    import math
    items, total = await ResearchRepository(db).list_by_year(academic_year, department_id, page, size, search)
    return s.PaginatedResearch(
        items=[s.ResearchPublicationRead.model_validate(i) for i in items],
        total=total, page=page, size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.post("/research", response_model=s.ResearchPublicationRead, status_code=201)
async def create_research(
    data: s.ResearchPublicationCreate,
    current_user: User = Depends(require_permission("research:create")),
    db: AsyncSession = Depends(get_db),
):
    item = await ResearchRepository(db).create(**data.model_dump())
    return s.ResearchPublicationRead.model_validate(item)


@router.put("/research/{record_id}", response_model=s.ResearchPublicationRead)
async def update_research(
    record_id: uuid.UUID,
    data: s.ResearchPublicationUpdate,
    current_user: User = Depends(require_permission("research:update")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = ResearchRepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    item = await repo.update(item, **data.model_dump(exclude_unset=True))
    return s.ResearchPublicationRead.model_validate(item)


@router.delete("/research/{record_id}", status_code=204)
async def delete_research(
    record_id: uuid.UUID,
    current_user: User = Depends(require_permission("research:delete")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = ResearchRepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    await repo.delete(item)


# ── Patents ───────────────────────────────────────────────────────────────────

@router.get("/patents", response_model=s.PaginatedPatents)
async def list_patents(
    academic_year: str = Query(...),
    department_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    page: int = 1, size: int = 20,
    current_user: User = Depends(require_permission("research:read")),
    db: AsyncSession = Depends(get_db),
):
    import math
    items, total = await PatentRepository(db).list_by_year(academic_year, department_id, page, size, search)
    return s.PaginatedPatents(
        items=[s.PatentRead.model_validate(i) for i in items],
        total=total, page=page, size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.post("/patents", response_model=s.PatentRead, status_code=201)
async def create_patent(
    data: s.PatentCreate,
    current_user: User = Depends(require_permission("research:create")),
    db: AsyncSession = Depends(get_db),
):
    item = await PatentRepository(db).create(**data.model_dump())
    return s.PatentRead.model_validate(item)


@router.put("/patents/{record_id}", response_model=s.PatentRead)
async def update_patent(
    record_id: uuid.UUID,
    data: s.PatentUpdate,
    current_user: User = Depends(require_permission("research:update")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = PatentRepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    item = await repo.update(item, **data.model_dump(exclude_unset=True))
    return s.PatentRead.model_validate(item)


# ── Placements ────────────────────────────────────────────────────────────────

@router.get("/placements", response_model=s.PaginatedPlacements)
async def list_placements(
    academic_year: str = Query(...),
    department_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    page: int = 1, size: int = 20,
    current_user: User = Depends(require_permission("placements:read")),
    db: AsyncSession = Depends(get_db),
):
    import math
    items, total = await PlacementRepository(db).list_by_year(academic_year, department_id, page, size, search)
    return s.PaginatedPlacements(
        items=[s.PlacementRead.model_validate(i) for i in items],
        total=total, page=page, size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.post("/placements", response_model=s.PlacementRead, status_code=201)
async def create_placement(
    data: s.PlacementCreate,
    current_user: User = Depends(require_permission("placements:create")),
    db: AsyncSession = Depends(get_db),
):
    item = await PlacementRepository(db).create(**data.model_dump())
    return s.PlacementRead.model_validate(item)


@router.get("/placements/stats", response_model=dict)
async def placement_stats(
    academic_year: str = Query(...),
    current_user: User = Depends(require_permission("placements:read")),
    db: AsyncSession = Depends(get_db),
):
    return await PlacementRepository(db).stats_by_year(academic_year)


@router.put("/placements/{record_id}", response_model=s.PlacementRead)
async def update_placement(
    record_id: uuid.UUID,
    data: s.PlacementUpdate,
    current_user: User = Depends(require_permission("placements:update")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = PlacementRepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    item = await repo.update(item, **data.model_dump(exclude_unset=True))
    return s.PlacementRead.model_validate(item)


# ── Energy ────────────────────────────────────────────────────────────────────

@router.get("/energy", response_model=s.PaginatedEnergy)
async def list_energy(
    academic_year: str = Query(...),
    search: Optional[str] = None,
    page: int = 1, size: int = 50,
    current_user: User = Depends(require_permission("dashboard:read")),
    db: AsyncSession = Depends(get_db),
):
    import math
    items, total = await EnergyRepository(db).list_by_year(academic_year, page, size, search)
    return s.PaginatedEnergy(
        items=[s.EnergyRead.model_validate(i) for i in items],
        total=total, page=page, size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.post("/energy", response_model=s.EnergyRead, status_code=201)
async def create_energy(
    data: s.EnergyCreate,
    current_user: User = Depends(require_permission("faculty:create")),
    db: AsyncSession = Depends(get_db),
):
    item = await EnergyRepository(db).create(**data.model_dump())
    return s.EnergyRead.model_validate(item)


@router.get("/energy/totals", response_model=dict)
async def energy_totals(
    academic_year: str = Query(...),
    current_user: User = Depends(require_permission("dashboard:read")),
    db: AsyncSession = Depends(get_db),
):
    return await EnergyRepository(db).totals_by_year(academic_year)


@router.put("/energy/{record_id}", response_model=s.EnergyRead)
async def update_energy(
    record_id: uuid.UUID,
    data: s.EnergyUpdate,
    current_user: User = Depends(require_permission("faculty:update")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = EnergyRepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    item = await repo.update(item, **data.model_dump(exclude_unset=True))
    return s.EnergyRead.model_validate(item)


# ── MoUs ──────────────────────────────────────────────────────────────────────

@router.get("/mous", response_model=s.PaginatedMoUs)
async def list_mous(
    academic_year: str = Query(...),
    department_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    page: int = 1, size: int = 20,
    current_user: User = Depends(require_permission("faculty:read")),
    db: AsyncSession = Depends(get_db),
):
    import math
    items, total = await MoURepository(db).list_by_year(academic_year, department_id, page, size, search)
    return s.PaginatedMoUs(
        items=[s.MoURead.model_validate(i) for i in items],
        total=total, page=page, size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.post("/mous", response_model=s.MoURead, status_code=201)
async def create_mou(
    data: s.MoUCreate,
    current_user: User = Depends(require_permission("faculty:create")),
    db: AsyncSession = Depends(get_db),
):
    item = await MoURepository(db).create(**data.model_dump())
    return s.MoURead.model_validate(item)


@router.put("/mous/{record_id}", response_model=s.MoURead)
async def update_mou(
    record_id: uuid.UUID,
    data: s.MoUUpdate,
    current_user: User = Depends(require_permission("faculty:update")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = MoURepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    item = await repo.update(item, **data.model_dump(exclude_unset=True))
    return s.MoURead.model_validate(item)


# ── Events ────────────────────────────────────────────────────────────────────

@router.get("/events", response_model=s.PaginatedEvents)
async def list_events(
    academic_year: str = Query(...),
    department_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    page: int = 1, size: int = 20,
    current_user: User = Depends(require_permission("faculty:read")),
    db: AsyncSession = Depends(get_db),
):
    import math
    items, total = await EventRepository(db).list_by_year(academic_year, department_id, page, size, search)
    return s.PaginatedEvents(
        items=[s.EventRead.model_validate(i) for i in items],
        total=total, page=page, size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.post("/events", response_model=s.EventRead, status_code=201)
async def create_event(
    data: s.EventCreate,
    current_user: User = Depends(require_permission("faculty:create")),
    db: AsyncSession = Depends(get_db),
):
    item = await EventRepository(db).create(**data.model_dump())
    return s.EventRead.model_validate(item)


@router.put("/events/{record_id}", response_model=s.EventRead)
async def update_event(
    record_id: uuid.UUID,
    data: s.EventUpdate,
    current_user: User = Depends(require_permission("faculty:update")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = EventRepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    item = await repo.update(item, **data.model_dump(exclude_unset=True))
    return s.EventRead.model_validate(item)


# ── Accreditations ────────────────────────────────────────────────────────────

@router.get("/accreditations", response_model=list[s.AccreditationRead])
async def list_accreditations(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    items = await AccreditationRepository(db).list_active()
    return [s.AccreditationRead.model_validate(i) for i in items]


@router.post("/accreditations", response_model=s.AccreditationRead, status_code=201)
async def create_accreditation(
    data: s.AccreditationCreate,
    current_user: User = Depends(require_permission("master_data:manage")),
    db: AsyncSession = Depends(get_db),
):
    item = await AccreditationRepository(db).create(**data.model_dump())
    return s.AccreditationRead.model_validate(item)


# ── SDG Activities ────────────────────────────────────────────────────────────

@router.get("/sdg", response_model=s.PaginatedSDG)
async def list_sdg(
    academic_year: str = Query(...),
    sdg_goal: Optional[int] = Query(None, ge=1, le=17),
    search: Optional[str] = None,
    page: int = 1, size: int = 20,
    current_user: User = Depends(require_permission("faculty:read")),
    db: AsyncSession = Depends(get_db),
):
    import math
    items, total = await SDGRepository(db).list_by_year(academic_year, sdg_goal, page, size, search)
    return s.PaginatedSDG(
        items=[s.SDGActivityRead.model_validate(i) for i in items],
        total=total, page=page, size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.post("/sdg", response_model=s.SDGActivityRead, status_code=201)
async def create_sdg_activity(
    data: s.SDGActivityCreate,
    current_user: User = Depends(require_permission("faculty:create")),
    db: AsyncSession = Depends(get_db),
):
    item = await SDGRepository(db).create(**data.model_dump())
    return s.SDGActivityRead.model_validate(item)


@router.put("/sdg/{record_id}", response_model=s.SDGActivityRead)
async def update_sdg_activity(
    record_id: uuid.UUID,
    data: s.SDGActivityUpdate,
    current_user: User = Depends(require_permission("faculty:update")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = SDGRepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    item = await repo.update(item, **data.model_dump(exclude_unset=True))
    return s.SDGActivityRead.model_validate(item)


# ── Water ─────────────────────────────────────────────────────────────────────

@router.get("/water")
async def list_water(
    academic_year: str = Query(...),
    search: Optional[str] = None,
    page: int = 1, size: int = 50,
    current_user: User = Depends(require_permission("dashboard:read")),
    db: AsyncSession = Depends(get_db),
):
    import math
    items, total = await WaterRepository(db).list_by_year(academic_year, page, size, search)
    return {
        "items": [s.WaterRead.model_validate(i) for i in items],
        "total": total, "page": page, "size": size,
        "pages": math.ceil(total / size) if total else 0,
    }


@router.post("/water", response_model=s.WaterRead, status_code=201)
async def create_water(
    data: s.WaterCreate,
    current_user: User = Depends(require_permission("faculty:create")),
    db: AsyncSession = Depends(get_db),
):
    item = await WaterRepository(db).create(**data.model_dump())
    return s.WaterRead.model_validate(item)


@router.put("/water/{record_id}", response_model=s.WaterRead)
async def update_water(
    record_id: uuid.UUID,
    data: s.WaterUpdate,
    current_user: User = Depends(require_permission("faculty:update")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = WaterRepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    item = await repo.update(item, **data.model_dump(exclude_unset=True))
    return s.WaterRead.model_validate(item)


@router.delete("/water/{record_id}", status_code=204)
async def delete_water(
    record_id: uuid.UUID,
    current_user: User = Depends(require_permission("faculty:delete")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = WaterRepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    await repo.delete(item)


# ── Waste ─────────────────────────────────────────────────────────────────────

@router.get("/waste")
async def list_waste(
    academic_year: str = Query(...),
    search: Optional[str] = None,
    page: int = 1, size: int = 50,
    current_user: User = Depends(require_permission("dashboard:read")),
    db: AsyncSession = Depends(get_db),
):
    import math
    items, total = await WasteRepository(db).list_by_year(academic_year, page, size, search)
    return {
        "items": [s.WasteRead.model_validate(i) for i in items],
        "total": total, "page": page, "size": size,
        "pages": math.ceil(total / size) if total else 0,
    }


@router.post("/waste", response_model=s.WasteRead, status_code=201)
async def create_waste(
    data: s.WasteCreate,
    current_user: User = Depends(require_permission("faculty:create")),
    db: AsyncSession = Depends(get_db),
):
    item = await WasteRepository(db).create(**data.model_dump())
    return s.WasteRead.model_validate(item)


@router.put("/waste/{record_id}", response_model=s.WasteRead)
async def update_waste(
    record_id: uuid.UUID,
    data: s.WasteUpdate,
    current_user: User = Depends(require_permission("faculty:update")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = WasteRepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    item = await repo.update(item, **data.model_dump(exclude_unset=True))
    return s.WasteRead.model_validate(item)


@router.delete("/waste/{record_id}", status_code=204)
async def delete_waste(
    record_id: uuid.UUID,
    current_user: User = Depends(require_permission("faculty:delete")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = WasteRepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    await repo.delete(item)


# ── Awards ────────────────────────────────────────────────────────────────────

@router.get("/awards")
async def list_awards(
    academic_year: str = Query(...),
    department_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    page: int = 1, size: int = 20,
    current_user: User = Depends(require_permission("faculty:read")),
    db: AsyncSession = Depends(get_db),
):
    import math
    items, total = await AwardRepository(db).list_by_year(academic_year, department_id, page, size, search)
    return {
        "items": [s.AwardRead.model_validate(i) for i in items],
        "total": total, "page": page, "size": size,
        "pages": math.ceil(total / size) if total else 0,
    }


@router.post("/awards", response_model=s.AwardRead, status_code=201)
async def create_award(
    data: s.AwardCreate,
    current_user: User = Depends(require_permission("faculty:create")),
    db: AsyncSession = Depends(get_db),
):
    item = await AwardRepository(db).create(**data.model_dump())
    return s.AwardRead.model_validate(item)


@router.put("/awards/{record_id}", response_model=s.AwardRead)
async def update_award(
    record_id: uuid.UUID,
    data: s.AwardUpdate,
    current_user: User = Depends(require_permission("faculty:update")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = AwardRepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    item = await repo.update(item, **data.model_dump(exclude_unset=True))
    return s.AwardRead.model_validate(item)


@router.delete("/awards/{record_id}", status_code=204)
async def delete_award(
    record_id: uuid.UUID,
    current_user: User = Depends(require_permission("faculty:delete")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi import HTTPException
    repo = AwardRepository(db)
    item = await repo.get_by_id(record_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    await repo.delete(item)


# ── Funded Projects ───────────────────────────────────────────────────────────

@router.get("/funded_projects")
async def list_funded_projects(
    academic_year: str = Query(...),
    department_id: Optional[uuid.UUID] = None,
    page: int = 1, size: int = 20,
    current_user: User = Depends(require_permission("research:read")),
    db: AsyncSession = Depends(get_db),
):
    import math
    items, total = await ProjectRepository(db).list_by_year(academic_year, department_id, page, size)
    return {
        "items": [s.FundedProjectRead.model_validate(i) for i in items],
        "total": total, "page": page, "size": size,
        "pages": math.ceil(total / size) if total else 0,
    }


@router.post("/funded_projects", response_model=s.FundedProjectRead, status_code=201)
async def create_funded_project(
    data: s.FundedProjectCreate,
    current_user: User = Depends(require_permission("research:create")),
    db: AsyncSession = Depends(get_db),
):
    item = await ProjectRepository(db).create(**data.model_dump())
    return s.FundedProjectRead.model_validate(item)


# ── Higher Studies ────────────────────────────────────────────────────────────

@router.get("/higher_studies")
async def list_higher_studies(
    academic_year: str = Query(...),
    department_id: Optional[uuid.UUID] = None,
    page: int = 1, size: int = 20,
    current_user: User = Depends(require_permission("students:read")),
    db: AsyncSession = Depends(get_db),
):
    import math
    items, total = await HigherStudyRepository(db).list_by_year(academic_year, department_id, page, size)
    return {
        "items": [s.HigherStudyRead.model_validate(i) for i in items],
        "total": total, "page": page, "size": size,
        "pages": math.ceil(total / size) if total else 0,
    }


@router.post("/higher_studies", response_model=s.HigherStudyRead, status_code=201)
async def create_higher_study(
    data: s.HigherStudyCreate,
    current_user: User = Depends(require_permission("students:create")),
    db: AsyncSession = Depends(get_db),
):
    item = await HigherStudyRepository(db).create(**data.model_dump())
    return s.HigherStudyRead.model_validate(item)


# ── Consultancy ───────────────────────────────────────────────────────────────

@router.get("/consultancy")
async def list_consultancy(
    academic_year: str = Query(...),
    department_id: Optional[uuid.UUID] = None,
    page: int = 1, size: int = 20,
    current_user: User = Depends(require_permission("faculty:read")),
    db: AsyncSession = Depends(get_db),
):
    import math
    items, total = await ConsultancyRepository(db).list_by_year(academic_year, department_id, page, size)
    return {
        "items": [s.ConsultancyRead.model_validate(i) for i in items],
        "total": total, "page": page, "size": size,
        "pages": math.ceil(total / size) if total else 0,
    }


@router.post("/consultancy", response_model=s.ConsultancyRead, status_code=201)
async def create_consultancy(
    data: s.ConsultancyCreate,
    current_user: User = Depends(require_permission("faculty:create")),
    db: AsyncSession = Depends(get_db),
):
    item = await ConsultancyRepository(db).create(**data.model_dump())
    return s.ConsultancyRead.model_validate(item)