"""Upload job tracking model."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    JSON, Boolean, DateTime, Enum, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class UploadStatus(str, enum.Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    COMPLETED  = "completed"
    FAILED     = "failed"
    PARTIAL    = "partial"   # some rows succeeded, some failed


class UploadEntityType(str, enum.Enum):
    FACULTY       = "faculty"
    STUDENTS      = "students"
    RESEARCH      = "research"
    PATENTS       = "patents"
    PLACEMENTS    = "placements"
    HIGHER_STUDIES = "higher_studies"
    PROJECTS      = "funded_projects"
    MOUS          = "mous"
    EVENTS        = "events"
    ENERGY        = "energy"
    WATER         = "water"
    WASTE         = "waste"
    AWARDS        = "awards"
    CONSULTANCY   = "consultancy"
    SDG           = "sdg_activities"


class UploadJob(BaseModel):
    """
    Tracks every Excel upload attempt.
    Stores validation results and row-level errors for audit and debugging.
    """
    __tablename__ = "upload_jobs"

    # Who / what
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    entity_type: Mapped[UploadEntityType] = mapped_column(
        Enum(UploadEntityType, values_callable=lambda obj: [e.value for e in obj]), nullable=False, index=True
    )
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    # File info
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    # Processing results
    status: Mapped[UploadStatus] = mapped_column(
        Enum(UploadStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=UploadStatus.PENDING, index=True
    )
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    inserted_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Detailed error log — stored as JSON array
    # Each item: {row: int, field: str, value: any, error: str}
    validation_errors: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Column mapping used (detected automatically)
    column_mapping: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Processing timestamps
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    uploader: Mapped["User"] = relationship("User")  # type: ignore

    def __repr__(self) -> str:
        return f"<UploadJob {self.entity_type} [{self.status}] {self.original_filename}>"
