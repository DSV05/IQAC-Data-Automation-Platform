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

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

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
        return instance

    async def update(self, instance: Any, **kwargs: Any) -> Any:
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.db.flush()
        await self.db.refresh(instance)
        return instance

    async def delete(self, instance: Any) -> None:
        await self.db.delete(instance)
        await self.db.flush()

    async def count(self, filters: Optional[List[Any]] = None) -> int:
        q = select(func.count()).select_from(self.model)
        if filters:
            from sqlalchemy import and_
            q = q.where(and_(*filters))
        return (await self.db.execute(q)).scalar_one()
