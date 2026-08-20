"""
Generic base repository.
Every master data repository extends this — avoiding duplicated CRUD code.
"""
import math
import uuid
from typing import Any, Generic, List, Optional, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

T = TypeVar("T")


class BaseRepository(Generic[T]):
    model: type

    def __init__(self, db: AsyncSession, actor: Any = None, source: str = "manual_edit") -> None:
        """
        actor: the currently-authenticated User performing this change, or
        None. When set, create()/update()/delete() automatically write an
        AuditLog entry with a before/after diff — every entity built on
        this base repository gets audit logging for free.

        source: "manual_edit" (default, e.g. the Master Data Edit modal)
        or "upload" (bulk Excel/CSV upload) — shown in the audit log so
        it's clear how a change was made.
        """
        self.db = db
        self.actor = actor
        self.source = source

    async def get_by_id(self, record_id: uuid.UUID) -> Optional[Any]:
        result = await self.db.execute(
            select(self.model).where(self.model.id == record_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        page: int = 1,
        size: int = 20,
        filters: Optional[List[Any]] = None,
        order_by: Any = None,
    ) -> tuple:
        query = select(self.model)
        count_q = select(func.count()).select_from(self.model)

        if filters:
            from sqlalchemy import and_
            query = query.where(and_(*filters))
            count_q = count_q.where(and_(*filters))

        total = (await self.db.execute(count_q)).scalar_one()

        if order_by is not None:
            query = query.order_by(order_by)
        else:
            query = query.order_by(self.model.created_at.desc())

        offset = (page - 1) * size
        result = await self.db.execute(query.offset(offset).limit(size))
        return list(result.scalars().all()), total

    async def create(self, **kwargs: Any) -> Any:
        instance = self.model(**kwargs)
        self.db.add(instance)
        await self.db.flush()
        await self.db.refresh(instance)
        if self.actor is not None:
            await self._log("create", instance, before=None)
        return instance

    async def update(self, instance: Any, **kwargs: Any) -> Any:
        before_snapshot = self._snapshot(instance) if self.actor is not None else None
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.db.flush()
        await self.db.refresh(instance)
        if self.actor is not None:
            await self._log("update", instance, before=before_snapshot)
        return instance

    async def delete(self, instance: Any) -> None:
        if self.actor is not None:
            before_snapshot = self._snapshot(instance)
            await self._log("delete", instance, before=before_snapshot, after_override={})
        await self.db.delete(instance)
        await self.db.flush()

    async def count(self, filters: Optional[List[Any]] = None) -> int:
        q = select(func.count()).select_from(self.model)
        if filters:
            from sqlalchemy import and_
            q = q.where(and_(*filters))
        return (await self.db.execute(q)).scalar_one()

    # ── Audit logging helpers ──────────────────────────────────────────────

    @staticmethod
    def _snapshot(instance: Any) -> dict:
        return {c.name: getattr(instance, c.name, None) for c in instance.__table__.columns}

    async def _log(self, action: str, instance: Any, before: dict | None, after_override: dict | None = None) -> None:
        from app.services.audit import record_change

        after = after_override if after_override is not None else self._snapshot(instance)
        await record_change(
            self.db,
            entity_type=self.model.__tablename__,
            entity_id=instance.id,
            action=action,
            changed_by=getattr(self.actor, "id", None),
            changed_by_name=getattr(self.actor, "full_name", None),
            before=before,
            after=after,
            academic_year=getattr(instance, "academic_year", None),
            source=self.source,
        )
