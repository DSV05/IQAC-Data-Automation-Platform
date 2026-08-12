"""Placement and higher studies outcome models."""
import uuid
from datetime import date

from sqlalchemy import (
    Boolean, Date, Enum, Float, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import Gender, PlacementType, StudentCategory


class Placement(BaseModel):
    """
    Student placement outcomes.
    NIRF Criterion V, NBA OBE outcomes.
    """
    __tablename__ = "placements"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id"), nullable=True, index=True
    )

    # Student info
    student_name: Mapped[str] = mapped_column(String(255), nullable=False)
    enrollment_no: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    category: Mapped[StudentCategory] = mapped_column(
        Enum(StudentCategory, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=StudentCategory.GENERAL
    )

    # Placement details
    placement_type: Mapped[PlacementType] = mapped_column(
        Enum(PlacementType, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=PlacementType.CAMPUS
    )
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    package_lpa: Mapped[float | None] = mapped_column(Float, nullable=True)  # LPA = Lakhs Per Annum
    placement_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Location
    company_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    company_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_international: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped["Department"] = relationship("Department")  # type: ignore


class HigherStudy(BaseModel):
    """Students pursuing higher education after graduation."""
    __tablename__ = "higher_studies"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("programs.id"), nullable=True
    )

    student_name: Mapped[str] = mapped_column(String(255), nullable=False)
    enrollment_no: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, values_callable=lambda obj: [e.value for e in obj]), nullable=False)

    # Admission details
    admitted_program: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "M.Tech CSE"
    admitted_institute: Mapped[str] = mapped_column(String(255), nullable=False)
    admitted_university: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
    entrance_exam: Mapped[str | None] = mapped_column(String(100), nullable=True)  # GATE, GRE, etc.
    entrance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    scholarship_received: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scholarship_amount: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped["Department"] = relationship("Department")  # type: ignore
