"""Infrastructure, budget, MoU, and events models."""
import uuid
from datetime import date

from sqlalchemy import (
    Boolean, Date, Enum, Float, ForeignKey,
    Integer, String, Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import EventType, MoUType


class Infrastructure(BaseModel):
    """Physical infrastructure data — classrooms, labs, library, etc."""
    __tablename__ = "infrastructure"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )

    facility_type: Mapped[str] = mapped_column(String(100), nullable=False)  # Classroom, Lab, Library
    facility_name: Mapped[str] = mapped_column(String(255), nullable=False)
    area_sqmt: Mapped[float | None] = mapped_column(Float, nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Lab specific
    is_lab: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    equipment_value: Mapped[float | None] = mapped_column(Float, nullable=True)

    # IT
    computers_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    internet_speed_mbps: Mapped[float | None] = mapped_column(Float, nullable=True)

    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    department: Mapped["Department | None"] = relationship("Department")  # type: ignore


class Budget(BaseModel):
    """Annual budget — income and expenditure heads."""
    __tablename__ = "budgets"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )

    head: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "Tuition Fees", "Salary"
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # income / expenditure
    sub_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    amount_budgeted: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    amount_actual: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped["Department | None"] = relationship("Department")  # type: ignore


class MoU(BaseModel):
    """Memoranda of Understanding with industry/academia."""
    __tablename__ = "mous"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )

    partner_name: Mapped[str] = mapped_column(String(255), nullable=False)
    partner_country: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
    partner_type: Mapped[MoUType] = mapped_column(Enum(MoUType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    mou_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    signed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    activities_conducted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    document_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped["Department | None"] = relationship("Department")  # type: ignore


class Event(BaseModel):
    """Conferences, workshops, FDPs, seminars organized/attended."""
    __tablename__ = "events"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    event_type: Mapped[EventType] = mapped_column(Enum(EventType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    is_organized: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # organized vs attended
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    venue: Mapped[str | None] = mapped_column(String(255), nullable=True)
    participants_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    faculty_participants: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    student_participants: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    external_participants: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_international: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    funding_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    sdg_goals: Mapped[str | None] = mapped_column(Text, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped["Department | None"] = relationship("Department")  # type: ignore
