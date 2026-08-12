"""Module 8 — Report Generator: generation audit log model."""
import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ReportType(str, enum.Enum):
    NIRF = "nirf"
    NAAC_SSR = "naac_ssr"
    AISHE = "aishe"


class ReportFormat(str, enum.Enum):
    XLSX = "xlsx"
    PDF = "pdf"


class ReportGenerationLog(BaseModel):
    """Audit trail of every generated report — who, what, when, how big."""
    __tablename__ = "report_generation_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType, values_callable=lambda obj: [e.value for e in obj]), nullable=False,
    )
    report_format: Mapped[ReportFormat] = mapped_column(
        Enum(ReportFormat, values_callable=lambda obj: [e.value for e in obj]), nullable=False,
    )
    academic_year: Mapped[str | None] = mapped_column(String(10), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped["User"] = relationship("User")  # type: ignore

    def __repr__(self) -> str:
        return f"<ReportGenerationLog {self.report_type}/{self.report_format} {self.academic_year}>"
