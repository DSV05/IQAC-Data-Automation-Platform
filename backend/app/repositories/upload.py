"""Repository for UploadJob model."""
import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.upload import UploadJob, UploadStatus
from app.repositories.base import BaseRepository


class UploadRepository(BaseRepository[UploadJob]):
    model = UploadJob

    async def get_with_uploader(self, job_id: uuid.UUID) -> UploadJob | None:
        result = await self.db.execute(
            select(UploadJob)
            .options(selectinload(UploadJob.uploader))
            .where(UploadJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        page: int = 1,
        size: int = 20,
        entity_type: str | None = None,
        status: UploadStatus | None = None,
    ) -> tuple[list[UploadJob], int]:
        filters = []
        if entity_type:
            filters.append(UploadJob.entity_type == entity_type)
        if status:
            filters.append(UploadJob.status == status)
        return await self.list(page=page, size=size, filters=filters or None)

    async def update_status(
        self,
        job: UploadJob,
        status: UploadStatus,
        **kwargs,
    ) -> UploadJob:
        return await self.update(job, status=status, **kwargs)

    async def get_stats(self) -> dict:
        """Dashboard-level upload statistics."""
        result = await self.db.execute(
            select(
                UploadJob.status,
                func.count().label("cnt"),
            ).group_by(UploadJob.status)
        )
        counts = {r.status.value: r.cnt for r in result}
        total = sum(counts.values())
        return {
            "total_uploads": total,
            "completed": counts.get("completed", 0),
            "failed": counts.get("failed", 0),
            "partial": counts.get("partial", 0),
            "pending": counts.get("pending", 0),
        }
