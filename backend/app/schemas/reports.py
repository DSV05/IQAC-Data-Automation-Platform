"""Module 8 — Report Generator — Pydantic schemas."""
import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class ReportTypeSchema(str, Enum):
    NIRF = "nirf"
    NAAC_SSR = "naac_ssr"
    AISHE = "aishe"


class ReportFormatSchema(str, Enum):
    XLSX = "xlsx"
    PDF = "pdf"


class ReportTypeInfo(BaseModel):
    value: str
    label: str
    description: str


class ReportHistoryItem(BaseModel):
    id: uuid.UUID
    report_type: ReportTypeSchema
    report_format: ReportFormatSchema
    academic_year: str | None
    file_size_bytes: int | None
    created_at: datetime

    class Config:
        from_attributes = True
