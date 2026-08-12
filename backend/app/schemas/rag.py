"""Module 7 — RAG Chatbot — Pydantic schemas."""
import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RAGDocumentTypeSchema(str, Enum):
    NAAC_SSR = "naac_ssr"
    ANNUAL_REPORT = "annual_report"
    NIRF_REPORT = "nirf_report"
    POLICY = "policy"
    OTHER = "other"


class RAGDocumentStatusSchema(str, Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class RAGDocumentItem(BaseModel):
    id: uuid.UUID
    title: str
    original_filename: str
    doc_type: RAGDocumentTypeSchema
    academic_year: str | None
    status: RAGDocumentStatusSchema
    page_count: int | None
    chunk_count: int | None
    file_size_bytes: int | None
    error_message: str | None
    uploaded_by_name: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class RAGChatRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)
    document_id: uuid.UUID | None = Field(None, description="Restrict the answer to one document")


class RAGSource(BaseModel):
    document_id: uuid.UUID
    title: str
    filename: str
    page: int
    snippet: str
    score: float


class RAGChatResponse(BaseModel):
    id: uuid.UUID
    question: str
    answer: str | None
    sources: list[RAGSource] = []
    status: str
    execution_ms: float | None
    error_message: str | None
    ai_provider: str | None


class RAGChatHistoryItem(BaseModel):
    id: uuid.UUID
    question: str
    answer: str | None
    status: str
    execution_ms: float | None
    error_message: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class RAGInfo(BaseModel):
    ai_configured: bool
    ai_provider: str
    document_count: int
    ready_document_count: int
