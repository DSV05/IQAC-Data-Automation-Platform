"""
Audit Log — records who changed what, old/new values, and when.

One row per create/update/delete on a master-data record. `changes` holds
a JSON diff: {"field_name": {"old": ..., "new": ...}, ...} — for creates,
`old` is always null; for deletes, `new` is always null; for updates, only
fields that actually changed are present.
"""
import enum
import uuid

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_changed_at", "created_at"),
    )

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    action: Mapped[str] = mapped_column(
        # Stored as plain string, not a DB-level enum type — keeps adding
        # future actions (e.g. "restore") migration-free. Values are the
        # AuditAction enum's .value strings ("create"/"update"/"delete").
        String(20), nullable=False,
    )

    # Denormalized so the log still reads correctly even if the user
    # account is later deleted or renamed.
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    changed_by_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    academic_year: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)

    # "manual_edit" (Master Data Edit modal) or "upload" (bulk Excel/CSV upload)
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="manual_edit")

    # {"field": {"old": ..., "new": ...}, ...}
    changes: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # A short human label for the record, captured at write time (e.g. a
    # faculty's full_name, a student's enrollment_no) so the log stays
    # readable without needing to join back to a row that may since have
    # changed further or, for deletes, no longer exists at all.
    entity_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
