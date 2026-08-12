"""Module 6 — AI Natural Language Search — Pydantic schemas."""
import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AIQueryStatusSchema(str, Enum):
    SUCCESS = "success"
    BLOCKED = "blocked"
    ERROR = "error"


class NLQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000, description="Natural language question")
    academic_year: str | None = Field(None, description="Optional academic year hint, e.g. '2023-24'")


class NLQueryResponse(BaseModel):
    id: uuid.UUID
    question: str
    generated_sql: str | None
    status: AIQueryStatusSchema
    columns: list[str] = []
    rows: list[dict] = []
    row_count: int = 0
    execution_ms: float | None = None
    truncated: bool = False
    explanation: str | None = None
    error_message: str | None = None
    ai_provider: str | None = None


class AIQueryHistoryItem(BaseModel):
    id: uuid.UUID
    question: str
    generated_sql: str | None
    status: AIQueryStatusSchema
    row_count: int | None
    execution_ms: float | None
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class AISchemaInfo(BaseModel):
    """Info the frontend can show about what's queryable, and whether AI is configured."""
    ai_configured: bool
    ai_provider: str
    tables: list[str]
    example_questions: list[str]
