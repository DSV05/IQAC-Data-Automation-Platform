"""Faculty master data model."""
import uuid
from datetime import date

from sqlalchemy import (
    Boolean, Date, Enum, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import (
    Designation, EmploymentType, Gender, Qualification,
)


class Faculty(BaseModel):
    """
    One row per faculty member per academic year.
    Allows tracking year-on-year changes in designation, qualification, etc.
    """
    __tablename__ = "faculty"
    __table_args__ = (
        UniqueConstraint("employee_id", "academic_year", name="uq_faculty_emp_year"),
    )

    # Identity
    employee_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # e.g. "2023-24"
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )

    # Personal
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    aadhaar_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)  # last 4 digits only

    # Academic
    designation: Mapped[Designation] = mapped_column(Enum(Designation, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    qualification: Mapped[Qualification] = mapped_column(Enum(Qualification, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phd_awarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    phd_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    phd_university: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Employment
    employment_type: Mapped[EmploymentType] = mapped_column(Enum(EmploymentType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    date_of_joining: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_of_leaving: Mapped[date | None] = mapped_column(Date, nullable=True)
    experience_teaching: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # years
    experience_industry: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    experience_research: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # NIRF specific
    # Nullable preserves existing records during the NIRF 2026 migration.
    institute: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_sanctioned_post: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    pan_number: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Flags
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    department: Mapped["Department"] = relationship("Department")  # type: ignore

    def __repr__(self) -> str:
        return f"<Faculty {self.employee_id}: {self.full_name} [{self.academic_year}]>"
