"""
Module 11 — Notifications
============================
NotificationService is the reusable helper other modules call to raise
an alert (e.g. Workflow calling `notify_user(...)` when a submission is
reviewed). DeadlineService manages the IQAC-defined dates that the
scheduled reminder job checks against.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.permissions import ROLE_LEVEL
from app.models.notification import Deadline, Notification, NotificationType
from app.models.user import User, UserRole


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def notify_user(
        self, user_id: uuid.UUID, type_: NotificationType, title: str, message: str, link: str | None = None
    ) -> Notification:
        note = Notification(user_id=user_id, type=type_, title=title, message=message, link=link)
        self.db.add(note)
        await self.db.flush()
        return note

    async def notify_department(
        self, department_id: uuid.UUID, type_: NotificationType, title: str, message: str, link: str | None = None
    ) -> int:
        """Notifies every active user in a department. Returns how many were notified."""
        result = await self.db.execute(
            select(User.id).where(User.department_id == department_id, User.is_active == True)  # noqa: E712
        )
        user_ids = [row[0] for row in result.all()]
        for uid in user_ids:
            await self.notify_user(uid, type_, title, message, link)
        return len(user_ids)

    async def notify_role_at_least(
        self, minimum_role: UserRole, type_: NotificationType, title: str, message: str, link: str | None = None
    ) -> int:
        """Notifies every active user whose role is at or above the given level (e.g. all IQAC Admins)."""
        min_level = ROLE_LEVEL[minimum_role]
        eligible_roles = [r for r, lvl in ROLE_LEVEL.items() if lvl >= min_level]
        result = await self.db.execute(
            select(User.id).where(User.role.in_(eligible_roles), User.is_active == True)  # noqa: E712
        )
        user_ids = [row[0] for row in result.all()]
        for uid in user_ids:
            await self.notify_user(uid, type_, title, message, link)
        return len(user_ids)

    async def list_for_user(self, user_id: uuid.UUID, unread_only: bool, limit: int) -> list[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)  # noqa: E712
        stmt = stmt.order_by(Notification.created_at.desc()).limit(min(limit, 100))
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def unread_count(self, user_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(Notification).where(
                Notification.user_id == user_id, Notification.is_read == False  # noqa: E712
            )
        )
        return result.scalar() or 0

    async def mark_read(self, user_id: uuid.UUID, notification_id: uuid.UUID) -> None:
        note = await self.db.get(Notification, notification_id)
        if note and note.user_id == user_id and not note.is_read:
            note.is_read = True
            note.read_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def mark_all_read(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )
        await self.db.commit()


class DeadlineNotFoundError(Exception):
    pass


class DeadlineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: uuid.UUID, payload) -> Deadline:
        deadline = Deadline(
            title=payload.title,
            description=payload.description,
            academic_year=payload.academic_year,
            due_date=payload.due_date,
            department_id=payload.department_id,
            reminder_days_before=payload.reminder_days_before,
            created_by=user_id,
        )
        self.db.add(deadline)
        await self.db.commit()
        await self.db.refresh(deadline, attribute_names=["department"])
        return deadline

    async def list(self) -> list[Deadline]:
        stmt = (
            select(Deadline)
            .options(selectinload(Deadline.department))
            .order_by(Deadline.due_date.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, deadline_id: uuid.UUID) -> None:
        deadline = await self.db.get(Deadline, deadline_id)
        if not deadline:
            raise DeadlineNotFoundError(f"Deadline {deadline_id} not found.")
        await self.db.delete(deadline)
        await self.db.commit()
