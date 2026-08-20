"""Audit Log endpoints — who changed what, old/new values, and when."""
import math
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.user import User
from app.repositories.audit import AuditLogRepository
from app.schemas import audit as s

router = APIRouter()


@router.get("", response_model=s.PaginatedAuditLogs)
async def list_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    changed_by: Optional[uuid.UUID] = None,
    action: Optional[str] = Query(None, description="create | update | delete"),
    source: Optional[str] = Query(None, description="manual_edit | upload"),
    academic_year: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    q: Optional[str] = Query(None, description="Free-text match on the record's label (name/title/etc.)"),
    page: int = 1,
    size: int = 50,
    current_user: User = Depends(require_permission("audit:read")),
    db: AsyncSession = Depends(get_db),
):
    items, total = await AuditLogRepository(db).search(
        entity_type=entity_type, entity_id=entity_id, changed_by=changed_by,
        action=action, source=source, academic_year=academic_year,
        date_from=date_from, date_to=date_to, q=q, page=page, size=size,
    )
    return s.PaginatedAuditLogs(
        items=[s.AuditLogRead.model_validate(i) for i in items],
        total=total, page=page, size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.get("/entity-types", response_model=list[str])
async def list_audit_entity_types(
    current_user: User = Depends(require_permission("audit:read")),
    db: AsyncSession = Depends(get_db),
):
    return await AuditLogRepository(db).distinct_entity_types()


@router.get("/entity/{entity_type}/{entity_id}", response_model=list[s.AuditLogRead])
async def entity_audit_history(
    entity_type: str,
    entity_id: uuid.UUID,
    current_user: User = Depends(require_permission("audit:read")),
    db: AsyncSession = Depends(get_db),
):
    """Full change history for one specific record — used by a "History" button on a row."""
    items, _ = await AuditLogRepository(db).search(
        entity_type=entity_type, entity_id=entity_id, page=1, size=500,
    )
    return [s.AuditLogRead.model_validate(i) for i in items]
