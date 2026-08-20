"""
Audit recording — computes old/new diffs and writes an AuditLog row.

Called from BaseRepository.create()/update() whenever the repo was given
an `actor` (see repositories/base.py), so every entity that goes through
the shared repository layer gets audit logging automatically — no need to
hand-instrument each individual endpoint.
"""
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog

# Columns that are never worth logging — internal bookkeeping, not data a
# person changed.
_IGNORED_FIELDS = {"id", "created_at", "updated_at"}

# Per entity_type, which field to use as a human-readable label in the log
# (falls back to entity_id if the entity has none of these).
_LABEL_FIELDS = [
    "full_name", "title", "partner_name", "student_name", "recipient_name",
    "company_name", "employee_id", "enrollment_no", "name",
]


def _pick_label(values: dict[str, Any]) -> str | None:
    for field in _LABEL_FIELDS:
        if values.get(field):
            return str(values[field])
    return None


def _serializable(value: Any) -> Any:
    """JSON columns can't store UUIDs/dates/enums directly — stringify anything non-primitive."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, uuid.UUID):
        return str(value)
    if hasattr(value, "value") and hasattr(value, "name"):  # enum.Enum member
        return value.value
    return str(value)


async def record_change(
    db: AsyncSession,
    *,
    entity_type: str,
    entity_id: uuid.UUID,
    action: str,  # "create" | "update" | "delete"
    changed_by: uuid.UUID | None,
    changed_by_name: str | None,
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    academic_year: str | None = None,
    source: str = "manual_edit",
) -> None:
    before = before or {}
    after = after or {}

    if action == "update":
        changes = {
            field: {"old": _serializable(before.get(field)), "new": _serializable(after.get(field))}
            for field in after
            if field not in _IGNORED_FIELDS and before.get(field) != after.get(field)
        }
        if not changes:
            return  # nothing actually changed — don't clutter the log
    elif action == "create":
        changes = {
            field: {"old": None, "new": _serializable(value)}
            for field, value in after.items()
            if field not in _IGNORED_FIELDS and value is not None
        }
    else:  # delete
        changes = {
            field: {"old": _serializable(value), "new": None}
            for field, value in before.items()
            if field not in _IGNORED_FIELDS and value is not None
        }

    label = _pick_label(after) or _pick_label(before)

    log = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        changed_by=changed_by,
        changed_by_name=changed_by_name,
        academic_year=academic_year or after.get("academic_year") or before.get("academic_year"),
        source=source,
        changes=changes,
        entity_label=label,
    )
    db.add(log)
    await db.flush()
