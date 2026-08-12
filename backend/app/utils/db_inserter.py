"""
Database Inserter — inserts validated rows into master tables.
"""
import uuid
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.master import (
    EnergyRepository, EventRepository, FacultyRepository,
    MoURepository, PatentRepository, PlacementRepository,
    ResearchRepository, StudentRepository,
)


async def insert_rows(
    db: AsyncSession,
    entity_type: str,
    valid_rows: list[dict],
    department_id: uuid.UUID | None = None,
    mode: str = "insert",
) -> tuple[int, int, int]:
    inserted = 0
    updated = 0
    skipped = 0

    # Inject department_id if provided and not already set
    if department_id:
        for row in valid_rows:
            if not row.get("department_id"):
                row["department_id"] = department_id

    if entity_type == "faculty":
        repo = FacultyRepository(db)
        for row in valid_rows:
            # Ensure required department_id exists
            if not row.get("department_id"):
                continue  # skip rows without department
            existing = await repo.get_by_employee_year(
                row.get("employee_id", ""), row.get("academic_year", "")
            )
            if existing:
                update_fields = {
                    k: v for k, v in row.items()
                    if k not in ("employee_id", "academic_year", "department_id")
                }
                if update_fields:
                    await repo.update(existing, **update_fields)
                    updated += 1
                else:
                    skipped += 1
            elif mode == "update":
                # Update Mode + no matching employee found — the file likely only
                # has the key plus a couple of fields, not a full faculty record,
                # so skip rather than attempt an incomplete (and likely invalid) insert.
                skipped += 1
            else:
                await repo.create(**row)
                inserted += 1

    elif entity_type == "students":
        repo = StudentRepository(db)
        for row in valid_rows:
            existing = await repo.get_by_enrollment_year(
                str(row.get("enrollment_no", "")), row.get("academic_year", "")
            )
            if existing:
                update_fields = {
                    k: v for k, v in row.items()
                    if k not in ("enrollment_no", "academic_year")
                }
                if update_fields:
                    await repo.update(existing, **update_fields)
                    updated += 1
                else:
                    skipped += 1
            elif mode == "update":
                # Update Mode + no matching student found — the file likely only
                # has the key plus a couple of fields (e.g. just CGPA), not a
                # full student record, so skip rather than attempt a bad insert.
                skipped += 1
            elif not row.get("program_id"):
                # A brand-new student needs a program — without it the insert
                # would violate a NOT NULL constraint and (without a savepoint)
                # could abort the rest of the batch, so skip cleanly instead.
                skipped += 1
            else:
                try:
                    async with db.begin_nested():
                        await repo.create(**row)
                    inserted += 1
                except IntegrityError:
                    skipped += 1

    elif entity_type == "research":
        repo = ResearchRepository(db)
        for row in valid_rows:
            if not row.get("department_id"):
                continue
            # Deduplicate by DOI
            if row.get("doi"):
                from sqlalchemy import select
                from app.models.research import ResearchPublication
                result = await db.execute(
                    select(ResearchPublication).where(
                        ResearchPublication.doi == row["doi"],
                        ResearchPublication.academic_year == row.get("academic_year"),
                    )
                )
                existing = result.scalar_one_or_none()
                if existing:
                    await repo.update(existing, citations=row.get("citations", existing.citations))
                    updated += 1
                    continue
            await repo.create(**row)
            inserted += 1

    elif entity_type == "patents":
        repo = PatentRepository(db)
        for row in valid_rows:
            if not row.get("department_id"):
                continue
            await repo.create(**row)
            inserted += 1

    elif entity_type == "placements":
        repo = PlacementRepository(db)
        for row in valid_rows:
            if not row.get("department_id"):
                continue
            await repo.create(**row)
            inserted += 1

    elif entity_type == "energy":
        repo = EnergyRepository(db)
        for row in valid_rows:
            await repo.create(**row)
            inserted += 1

    elif entity_type == "mous":
        repo = MoURepository(db)
        for row in valid_rows:
            await repo.create(**row)
            inserted += 1

    elif entity_type == "events":
        repo = EventRepository(db)
        for row in valid_rows:
            await repo.create(**row)
            inserted += 1

    else:
        # For entity types without a specific inserter, skip silently
        # They will be added as each module is completed
        pass

    return inserted, updated, skipped
