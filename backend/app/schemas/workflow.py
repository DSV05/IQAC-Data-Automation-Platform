"""Module 10 — Workflow & Approvals — Pydantic schemas."""
import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class WorkflowStatusSchema(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"
    LOCKED = "locked"


class SubmitRequest(BaseModel):
    department_id: uuid.UUID
    academic_year: str = Field(..., min_length=4, max_length=10)
    comments: str | None = None


class ReviewDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


class ReviewRequest(BaseModel):
    decision: ReviewDecision
    comments: str | None = None


class SubmissionItem(BaseModel):
    id: uuid.UUID
    department_id: uuid.UUID
    department_name: str
    academic_year: str
    status: WorkflowStatusSchema
    version: int
    submitted_by_name: str | None
    submitted_at: datetime | None
    reviewed_by_name: str | None
    reviewed_at: datetime | None
    review_comments: str | None
    locked_by_name: str | None
    locked_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class HistoryItem(BaseModel):
    id: uuid.UUID
    from_status: WorkflowStatusSchema | None
    to_status: WorkflowStatusSchema
    version: int
    actor_name: str | None
    comments: str | None
    created_at: datetime

    class Config:
        from_attributes = True
