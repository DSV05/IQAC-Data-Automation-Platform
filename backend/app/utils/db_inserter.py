"""
Database Inserter — generic ID-based upsert engine.
=====================================================
Every exported/template file carries a hidden "Record ID" column (see
excel_validator.py's RECORD_ID_FIELD). On upload:

  - Row has a Record ID that matches an existing row -> only the fields
    that actually changed are written (an untouched cell stays untouched).
  - Row has no Record ID, or the ID doesn't match anything -> inserted as
    a brand-new row.

This works identically for every entity type — there is no per-entity
"natural key" guessing anymore. A data operator can download the current
data, add new rows at the bottom, edit any existing row's cells, leave
everything else exactly as it was, and upload the same file back.
"""
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.master import (
    AwardRepository, EnergyRepository, EventRepository, FacultyRepository,
    MoURepository, PatentRepository, PlacementRepository, ProjectRepository, ResearchRepository,
    SDGRepository, StudentRepository, WasteRepository, WaterRepository,
    ConsultancyRepository,
)

# entity_type -> RepositoryClass. Matching on upload is always by Record ID
# (see below) — this map is just how we find the right repo per entity.
_REPO_MAP: dict[str, type] = {
    "faculty": FacultyRepository,
    "students": StudentRepository,
    "research": ResearchRepository,
    "patents": PatentRepository,
    "placements": PlacementRepository,
    "funded_projects": ProjectRepository,
    "consultancy": ConsultancyRepository,
    "mous": MoURepository,
    "events": EventRepository,
    "energy": EnergyRepository,
    "water": WaterRepository,
    "waste": WasteRepository,
    "awards": AwardRepository,
    "sdg_activities": SDGRepository,
}

# entity_type -> fields required to be present for a NEW insert to succeed
# without violating a DB NOT NULL constraint. NOT used for matching — only
# to skip a single row cleanly instead of crashing the whole batch on a
# foreign-key violation.
_INSERT_REQUIRES: dict[str, list[str]] = {
    "faculty": ["department_id"],
    "students": ["department_id"],
    "research": ["department_id"],
    "patents": ["department_id"],
    "placements": ["department_id"],
    "funded_projects": ["department_id"],
    "consultancy": ["department_id"],
    # mous, events, energy, water, waste, awards, sdg_activities: no
    # required FK — safe to insert with whatever the row provides.
}


async def insert_rows(
    db: AsyncSession,
    entity_type: str,
    valid_rows: list[dict],
    mode: str = "insert",  # kept for API compatibility; matching is always by Record ID now
    actor: object | None = None,  # the uploading User, for audit logging
) -> tuple[int, int, int]:
    inserted = 0
    updated = 0
    skipped = 0

    repo_cls = _REPO_MAP.get(entity_type)
    if repo_cls is None:
        # Entity not yet wired up for upload at all (e.g. consultancy,
        # higher_studies, funded_projects) — nothing to do.
        return 0, 0, 0

    repo = repo_cls(db, actor=actor, source="upload")
    required_for_insert = _INSERT_REQUIRES.get(entity_type, [])

    for row in valid_rows:
        # Relationship display values and validator metadata must never reach
        # SQLAlchemy's model constructor/update calls.
        row.pop("_row_number", None)
        row.pop("department", None)
        custom_values = row.pop("_custom_fields", None)
        record_id_raw = row.pop("_record_id", None)
        record_id: uuid.UUID | None = None
        if record_id_raw:
            try:
                record_id = uuid.UUID(str(record_id_raw))
            except (ValueError, AttributeError):
                record_id = None  # malformed/stray value — treat as a new row, don't error out

        existing = await repo.get_by_id(record_id) if record_id else None

        if existing is not None:
            # Only write fields that actually changed, so untouched cells
            # never overwrite good data with a stale re-upload.
            changed = {
                k: v for k, v in row.items()
                if k != "academic_year" and getattr(existing, k, object()) != v
            }
            if custom_values:
                merged_custom = {**(existing.custom_fields or {}), **custom_values}
                if merged_custom != (existing.custom_fields or {}):
                    changed["custom_fields"] = merged_custom
            if changed:
                await repo.update(existing, **changed)
                updated += 1
            else:
                skipped += 1
            continue

        # New row (no Record ID, or the ID didn't match anything we have —
        # e.g. someone copy-pasted a row from a different year's export).
        if any(not row.get(f) for f in required_for_insert):
            # Would violate a NOT NULL constraint — skip this one row only,
            # rest of the batch proceeds normally.
            skipped += 1
            continue
        if custom_values:
            row["custom_fields"] = custom_values
        try:
            async with db.begin_nested():
                await repo.create(**row)
            inserted += 1
        except IntegrityError:
            skipped += 1

    return inserted, updated, skipped
