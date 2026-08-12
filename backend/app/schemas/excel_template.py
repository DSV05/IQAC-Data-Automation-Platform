"""Module 9 — Excel Auto-Fill — Pydantic schemas."""
import uuid
from datetime import datetime

from pydantic import BaseModel


class ExcelTemplateItem(BaseModel):
    id: uuid.UUID
    title: str
    original_filename: str
    sheet_count: int | None
    token_count: int | None
    file_size_bytes: int | None
    uploaded_by_name: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenInfo(BaseModel):
    token: str
    sample_value: object
    group: str


class FillRequest(BaseModel):
    academic_year: str | None = None


class FillHistoryItem(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID | None
    academic_year: str | None
    tokens_filled: int
    tokens_missing: list[str] | None
    error_message: str | None
    file_size_bytes: int | None
    created_at: datetime

    class Config:
        from_attributes = True
