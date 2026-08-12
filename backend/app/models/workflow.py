"""
Module 10 — Workflow & Approvals
===================================
Submit → Department resubmission (after rejection) → IQAC approve → Lock.

One WorkflowSubmission row per (department, academic_year), evolving
through statuses. Every transition is appended to WorkflowHistoryEntry —
that's the version history.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class WorkflowStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    LOCKED = "locked"


class WorkflowSubmission(BaseModel):
    __tablename__ = "workflow_submissions"
    __table_args__ = (UniqueConstraint("department_id", "academic_year", name="uq_workflow_dept_year"),)

    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False, default=WorkflowStatus.DRAFT,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    locked_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    department: Mapped["Department"] = relationship("Department")  # type: ignore
    submitter: Mapped["User"] = relationship("User", foreign_keys=[submitted_by])  # type: ignore
    reviewer: Mapped["User"] = relationship("User", foreign_keys=[reviewed_by])  # type: ignore
    locker: Mapped["User"] = relationship("User", foreign_keys=[locked_by])  # type: ignore

    def __repr__(self) -> str:
        return f"<WorkflowSubmission dept={self.department_id} year={self.academic_year} [{self.status}] v{self.version}>"


class WorkflowHistoryEntry(BaseModel):
    """One row per status transition — the version history trail."""
    __tablename__ = "workflow_history"

    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_submissions.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    from_status: Mapped[WorkflowStatus | None] = mapped_column(
        Enum(WorkflowStatus, values_callable=lambda obj: [e.value for e in obj], name="workflowstatus"),
        nullable=True,
    )
    to_status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus, values_callable=lambda obj: [e.value for e in obj], name="workflowstatus"),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    submission: Mapped["WorkflowSubmission"] = relationship("WorkflowSubmission")
    actor: Mapped["User"] = relationship("User")  # type: ignore

    def __repr__(self) -> str:
        return f"<WorkflowHistoryEntry {self.from_status}->{self.to_status} v{self.version}>"
