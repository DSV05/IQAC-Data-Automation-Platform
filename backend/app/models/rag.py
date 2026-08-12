"""Module 7 — RAG Chatbot: document library and chat audit log models."""
import enum
import uuid

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class RAGDocumentType(str, enum.Enum):
    NAAC_SSR = "naac_ssr"
    ANNUAL_REPORT = "annual_report"
    NIRF_REPORT = "nirf_report"
    POLICY = "policy"
    OTHER = "other"


class RAGDocumentStatus(str, enum.Enum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class RAGChatStatus(str, enum.Enum):
    SUCCESS = "success"
    ERROR = "error"


class RAGDocument(BaseModel):
    """
    A PDF ingested into the RAG knowledge base (NAAC SSR, Annual Reports,
    NIRF submissions, policy documents, etc). Its extracted chunks live
    inside the FAISS vector index on disk; this row tracks status,
    metadata, and which vector ids belong to it (so it can be deleted
    from the index later without rebuilding everything from scratch).
    """
    __tablename__ = "rag_documents"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(300), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(300), nullable=False)
    doc_type: Mapped[RAGDocumentType] = mapped_column(
        Enum(RAGDocumentType, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False, default=RAGDocumentType.OTHER,
    )
    academic_year: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[RAGDocumentStatus] = mapped_column(
        Enum(RAGDocumentStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False, default=RAGDocumentStatus.PROCESSING,
    )
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    vector_ids: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)

    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    uploader: Mapped["User"] = relationship("User")  # type: ignore

    def __repr__(self) -> str:
        return f"<RAGDocument {self.title!r} [{self.status}]>"


class RAGChatLog(BaseModel):
    """Audit trail of every RAG chatbot question, answer, and cited sources."""
    __tablename__ = "rag_chat_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    sources: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[RAGChatStatus] = mapped_column(
        Enum(RAGChatStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False, default=RAGChatStatus.SUCCESS,
    )
    execution_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)

    user: Mapped["User"] = relationship("User")  # type: ignore

    def __repr__(self) -> str:
        return f"<RAGChatLog {self.id} [{self.status}] {self.question[:40]!r}>"
