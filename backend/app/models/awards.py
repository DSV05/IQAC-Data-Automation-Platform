"""Awards, accreditations, consultancy, and SDG activity models."""
import uuid
from datetime import date

from sqlalchemy import (
    Boolean, Date, Enum, Float, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import SDGGoal


class Award(BaseModel):
    """Awards and recognitions received by faculty, students, or institution."""
    __tablename__ = "awards"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    awarding_body: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_type: Mapped[str] = mapped_column(String(50), nullable=False)  # faculty/student/institution
    award_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_national: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_international: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    prize_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped["Department | None"] = relationship("Department")  # type: ignore


class Accreditation(BaseModel):
    """Institutional and program accreditations — NAAC, NBA, ISO, etc."""
    __tablename__ = "accreditations"

    name: Mapped[str] = mapped_column(String(100), nullable=False)  # NAAC, NBA, ISO 9001
    awarding_body: Mapped[str] = mapped_column(String(255), nullable=False)
    program_department: Mapped[str | None] = mapped_column(String(255), nullable=True)  # if program-specific
    grade_score: Mapped[str | None] = mapped_column(String(50), nullable=True)  # e.g. "A++" or "3.67"
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    cycle: Mapped[int | None] = mapped_column(Integer, nullable=True)  # NAAC cycle number
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    certificate_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)


class Consultancy(BaseModel):
    """Consultancy revenue from industry."""
    __tablename__ = "consultancies"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(Text, nullable=False)
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    faculty_names: Mapped[str] = mapped_column(Text, nullable=False)
    faculty_employee_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount_inr: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_ongoing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped["Department"] = relationship("Department")  # type: ignore


class SDGActivity(BaseModel):
    """Activities mapped to UN Sustainable Development Goals."""
    __tablename__ = "sdg_activities"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # research / teaching / community / policy / infrastructure
    sdg_primary: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 1-17
    sdg_secondary: Mapped[str | None] = mapped_column(Text, nullable=True)  # CSV
    beneficiaries_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    investment_inr: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped["Department | None"] = relationship("Department")  # type: ignore
