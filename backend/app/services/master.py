"""
Master Data Service
===================
Thin business logic layer over the repositories.
Handles: year validation, duplicate checks, pagination math.
"""
import math
import uuid
from typing import Any

from fastapi import HTTPException, status

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


def _paginate(items: list, total: int, page: int, size: int) -> dict:
    return {
        "items": items,
        "total": total,
        "page": page,
        "size": size,
        "pages": math.ceil(total / size) if total else 0,
    }


def _read(schema, items):
    return [schema.model_validate(i) for i in items]


# ── Faculty Service ───────────────────────────────────────────────────────────

class FacultyService:
    def __init__(self, repo: FacultyRepository):
        self.repo = repo

    async def list(self, academic_year: str, department_id=None,
                   page=1, size=20, search=None) -> s.PaginatedFaculty:
        items, total = await self.repo.list_by_year(
            academic_year, department_id, page, size, search
        )
        return s.PaginatedFaculty(**_paginate(_read(s.FacultyRead, items), total, page, size))

    async def create(self, data: s.FacultyCreate) -> s.FacultyRead:
        existing = await self.repo.get_by_employee_year(data.employee_id, data.academic_year)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Faculty '{data.employee_id}' already exists for {data.academic_year}",
            )
        item = await self.repo.create(**data.model_dump())
        return s.FacultyRead.model_validate(item)

    async def update(self, record_id: uuid.UUID, data: s.FacultyUpdate) -> s.FacultyRead:
        item = await self.repo.get_by_id(record_id)
        if not item:
            raise HTTPException(status_code=404, detail="Faculty record not found")
        item = await self.repo.update(item, **data.model_dump(exclude_unset=True))
        return s.FacultyRead.model_validate(item)

    async def delete(self, record_id: uuid.UUID) -> None:
        item = await self.repo.get_by_id(record_id)
        if not item:
            raise HTTPException(status_code=404, detail="Faculty record not found")
        await self.repo.delete(item)

    async def get(self, record_id: uuid.UUID) -> s.FacultyRead:
        item = await self.repo.get_by_id(record_id)
        if not item:
            raise HTTPException(status_code=404, detail="Faculty record not found")
        return s.FacultyRead.model_validate(item)

    async def summary(self, academic_year: str) -> dict:
        return await self.repo.count_by_year(academic_year)


# ── Generic service factory ───────────────────────────────────────────────────
# For entities that follow a simple CRUD + list_by_year pattern,
# we use a generic service to avoid repetition.

class _GenericMasterService:
    """Reusable base for simple master data entities."""

    def __init__(self, repo, read_schema, create_schema, update_schema, list_schema):
        self.repo = repo
        self.Read = read_schema
        self.Create = create_schema
        self.Update = update_schema
        self.List = list_schema

    async def list_by_year(self, academic_year: str, department_id=None,
                           page=1, size=20, **kwargs):
        items, total = await self.repo.list_by_year(
            academic_year, department_id=department_id, page=page, size=size, **kwargs
        )
        return self.List(**_paginate(_read(self.Read, items), total, page, size))

    async def get(self, record_id: uuid.UUID):
        item = await self.repo.get_by_id(record_id)
        if not item:
            raise HTTPException(status_code=404, detail="Record not found")
        return self.Read.model_validate(item)

    async def create(self, data) -> Any:
        item = await self.repo.create(**data.model_dump())
        return self.Read.model_validate(item)

    async def update(self, record_id: uuid.UUID, data) -> Any:
        item = await self.repo.get_by_id(record_id)
        if not item:
            raise HTTPException(status_code=404, detail="Record not found")
        item = await self.repo.update(item, **data.model_dump(exclude_unset=True))
        return self.Read.model_validate(item)

    async def delete(self, record_id: uuid.UUID) -> None:
        item = await self.repo.get_by_id(record_id)
        if not item:
            raise HTTPException(status_code=404, detail="Record not found")
        await self.repo.delete(item)


def make_service(repo, read_schema, create_schema, update_schema, list_schema):
    return _GenericMasterService(repo, read_schema, create_schema, update_schema, list_schema)
