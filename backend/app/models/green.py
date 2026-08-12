"""Green campus sustainability models — energy, water, waste."""
import uuid

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import WasteType


class EnergyConsumption(BaseModel):
    """Monthly/annual energy data for GHG emissions and green rankings."""
    __tablename__ = "energy_consumption"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 1-12; None = annual
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )

    # Grid electricity (Scope 2 GHG)
    electricity_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    electricity_cost_inr: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Renewable generation (Scope 2 reduction)
    solar_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    wind_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    other_renewable_kwh: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Diesel/fuel (Scope 1 GHG)
    diesel_liters: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    lpg_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    cng_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # Computed fields (can be derived; stored for reporting speed)
    ghg_scope1_tco2e: Mapped[float | None] = mapped_column(Float, nullable=True)
    ghg_scope2_tco2e: Mapped[float | None] = mapped_column(Float, nullable=True)

    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    department: Mapped["Department | None"] = relationship("Department")  # type: ignore


class WaterConsumption(BaseModel):
    """Water usage data for green rankings and sustainability reporting."""
    __tablename__ = "water_consumption"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True
    )

    # Sources (kiloliters)
    municipal_kl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    borewell_kl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rainwater_harvested_kl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recycled_treated_kl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    cost_inr: Mapped[float | None] = mapped_column(Float, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped["Department | None"] = relationship("Department")  # type: ignore


class WasteManagement(BaseModel):
    """Waste generation and disposal data."""
    __tablename__ = "waste_management"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)

    waste_type: Mapped[WasteType] = mapped_column(Enum(WasteType, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    generated_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recycled_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    disposed_kg: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    disposal_method: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cost_inr: Mapped[float | None] = mapped_column(Float, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)


class GreenInitiative(BaseModel):
    """Green campus initiatives — tree plantation, EV fleet, etc."""
    __tablename__ = "green_initiatives"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)  # Biodiversity, Transport, etc.
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    trees_planted: Mapped[int | None] = mapped_column(Integer, nullable=True)
    area_covered_sqmt: Mapped[float | None] = mapped_column(Float, nullable=True)
    investment_inr: Mapped[float | None] = mapped_column(Float, nullable=True)
    sdg_goals: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
