"""Student and Program master data models."""
import uuid
from datetime import date

from sqlalchemy import (
    Boolean, Date, Enum, ForeignKey,
    Integer, String, Text, UniqueConstraint, Float,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import (
    AdmissionType, Gender, ProgramLevel, StudentCategory,
)


class Program(BaseModel):
    """Academic programs offered by the university."""
    __tablename__ = "programs"
    __table_args__ = (
        UniqueConstraint("code", "academic_year", name="uq_program_code_year"),
    )

    code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )
    level: Mapped[ProgramLevel] = mapped_column(Enum(ProgramLevel, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    duration_years: Mapped[int] = mapped_column(Integer, nullable=False)
    intake_sanctioned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    intake_actual: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_nba_accredited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    nba_valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    department: Mapped["Department"] = relationship("Department")  # type: ignore

    def __repr__(self) -> str:
        return f"<Program {self.code}: {self.name}>"


class Student(BaseModel):
    """
    One row per student per academic year.
    Tracks enrollment, category, and key outcomes.
    """
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("enrollment_no", "academic_year", name="uq_student_enroll_year"),
    )

    # Identity
    enrollment_no: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    # Replaces the old program_id FK — a student now just carries its own
    # Level (UG/PG/Diploma/...) and Duration directly, instead of needing an
    # exact Program code to already exist for the department/year. The
    # Programs table still exists separately to hold sanctioned/actual
    # intake numbers for the NIRF template, keyed by (level, duration_years)
    # — it's no longer linked to individual students.
    level: Mapped[ProgramLevel] = mapped_column(
        Enum(ProgramLevel, values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    duration_years: Mapped[int] = mapped_column(Integer, nullable=False)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )

    # Personal
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    category: Mapped[StudentCategory] = mapped_column(
        Enum(StudentCategory, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=StudentCategory.GENERAL
    )
    is_pwd: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    state_of_domicile: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Admission
    admission_type: Mapped[AdmissionType] = mapped_column(
        Enum(AdmissionType, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=AdmissionType.REGULAR
    )
    year_of_admission: Mapped[int] = mapped_column(Integer, nullable=False)
    current_year: Mapped[int] = mapped_column(Integer, nullable=False)  # 1,2,3,4

    # Contact
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Academic performance
    sgpa_last: Mapped[float | None] = mapped_column(Float, nullable=True)
    cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    backlogs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Status
    is_lateral: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Only meaningful for level=phd — feeds the NIRF "Ph.D. Students" and
    # "Graduated Ph.D. Students" grids, which split full-time vs part-time.
    is_full_time: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    department: Mapped["Department"] = relationship("Department")  # type: ignore

    def __repr__(self) -> str:
        return f"<Student {self.enrollment_no}: {self.full_name} [{self.academic_year}]>"
