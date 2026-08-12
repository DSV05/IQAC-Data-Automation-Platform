"""
Module 11 — Notifications
============================
Two concerns:
  - Notification: an in-app alert for one user (missing data, deadline
    reminder, or a workflow approval/rejection/lock event).
  - Deadline: something an IQAC Admin defines (e.g. "NAAC SSR data entry
    deadline"), which the scheduled reminder job checks against.
"""
import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class NotificationType(str, enum.Enum):
    MISSING_DATA = "missing_data"
    DEADLINE_REMINDER = "deadline_reminder"
    WORKFLOW_SUBMITTED = "workflow_submitted"
    WORKFLOW_APPROVED = "workflow_approved"
    WORKFLOW_REJECTED = "workflow_rejected"
    WORKFLOW_LOCKED = "workflow_locked"
    GENERAL = "general"


class Notification(BaseModel):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False, default=NotificationType.GENERAL,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    link: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<Notification {self.type} user={self.user_id} read={self.is_read}>"


class Deadline(BaseModel):
    """A date IQAC wants departments reminded about (e.g. data entry cutoffs)."""
    __tablename__ = "deadlines"

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    academic_year: Mapped[str | None] = mapped_column(String(10), nullable=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=True,
    )
    reminder_days_before: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    last_reminded_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )

    department: Mapped["Department"] = relationship("Department")  # type: ignore

    def __repr__(self) -> str:
        return f"<Deadline {self.title!r} due={self.due_date}>"
