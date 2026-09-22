import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TimestampMixin:
    """Adds created_at / updated_at to any model."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    """UUID primary key — safer than sequential int for public-facing IDs."""
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class BaseModel(UUIDMixin, TimestampMixin, Base):
    """Abstract base every domain model extends."""
    __abstract__ = True

    # Values for admin-added "+ Add Column" fields (see custom_column.py).
    # Keyed by field_key -> string value. Nullable/absent on rows that
    # predate a given custom column, or on models with none defined yet.
    custom_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

