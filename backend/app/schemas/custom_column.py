"""Custom Columns — Pydantic schemas."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CustomColumnCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=200)


class CustomColumnItem(BaseModel):
    id: uuid.UUID
    entity_type: str
    field_key: str
    label: str
    created_at: datetime

    class Config:
        from_attributes = True
