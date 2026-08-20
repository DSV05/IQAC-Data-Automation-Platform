"""Repository for reading audit logs (writes happen automatically via BaseRepository)."""
import uuid
from datetime import datetime

from app.models.audit import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    model = AuditLog

    async def search(
        self,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        changed_by: uuid.UUID | None = None,
        action: str | None = None,
        source: str | None = None,
        academic_year: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        q: str | None = None,  # free-text match on entity_label
        page: int = 1,
        size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        filters = []
        if entity_type:
            filters.append(AuditLog.entity_type == entity_type)
        if entity_id:
            filters.append(AuditLog.entity_id == entity_id)
        if changed_by:
            filters.append(AuditLog.changed_by == changed_by)
        if action:
            filters.append(AuditLog.action == action)
        if source:
            filters.append(AuditLog.source == source)
        if academic_year:
            filters.append(AuditLog.academic_year == academic_year)
        if date_from:
            filters.append(AuditLog.created_at >= date_from)
        if date_to:
            filters.append(AuditLog.created_at <= date_to)
        if q:
            filters.append(AuditLog.entity_label.ilike(f"%{q}%"))

        return await self.list(page=page, size=size, filters=filters, order_by=AuditLog.created_at.desc())

    async def distinct_entity_types(self) -> list[str]:
        from sqlalchemy import select
        result = await self.db.execute(select(AuditLog.entity_type).distinct().order_by(AuditLog.entity_type))
        return [row[0] for row in result.all()]
