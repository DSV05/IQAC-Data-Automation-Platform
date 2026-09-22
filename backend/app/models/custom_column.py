"""Admin-defined extra columns for a Data Category's downloadable template.

Lets an IQAC Admin add a brand-new column (e.g. "LinkedIn URL") to any Data
Category from the "Edit Template" modal. The column immediately appears as
an extra header in that entity's downloaded Excel template. See
backend/app/api/v1/endpoints/custom_columns.py for the CRUD endpoints and
uploads.py::download_template for how these get merged into the sheet.
"""
import uuid

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CustomColumnDef(BaseModel):
    """One admin-added column definition, scoped to a single entity type."""
    __tablename__ = "custom_column_defs"
    __table_args__ = (
        UniqueConstraint("entity_type", "field_key", name="uq_custom_column_entity_key"),
    )

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    field_key: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=True,
    )

    def __repr__(self) -> str:
        return f"<CustomColumnDef {self.entity_type}.{self.field_key!r}>"
