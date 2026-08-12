"""Module 11 — Notifications — Pydantic schemas."""
import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class NotificationTypeSchema(str, Enum):
    MISSING_DATA = "missing_data"
    DEADLINE_REMINDER = "deadline_reminder"
    WORKFLOW_SUBMITTED = "workflow_submitted"
    WORKFLOW_APPROVED = "workflow_approved"
    WORKFLOW_REJECTED = "workflow_rejected"
    WORKFLOW_LOCKED = "workflow_locked"
    GENERAL = "general"


class NotificationItem(BaseModel):
    id: uuid.UUID
    type: NotificationTypeSchema
    title: str
    message: str
    link: str | None
    is_read: bool
    read_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class UnreadCountResponse(BaseModel):
    count: int


class DeadlineCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str | None = None
    academic_year: str | None = None
    due_date: date
    department_id: uuid.UUID | None = None
    reminder_days_before: int = Field(3, ge=0, le=90)


class DeadlineItem(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    academic_year: str | None
    due_date: date
    department_id: uuid.UUID | None
    department_name: str | None
    reminder_days_before: int
    last_reminded_on: date | None
    created_at: datetime

    class Config:
        from_attributes = True
