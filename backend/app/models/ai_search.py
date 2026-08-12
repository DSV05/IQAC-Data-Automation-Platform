"""Module 6 — AI Natural Language Search: query audit log model."""
import enum
import uuid

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class AIQueryStatus(str, enum.Enum):
    SUCCESS = "success"
    BLOCKED = "blocked"     # generated SQL failed the safety guard
    ERROR = "error"         # LLM error or DB execution error


class AIQueryLog(BaseModel):
    """
    Every natural-language question, the SQL generated for it, and the
    outcome. Gives IQAC Admins an audit trail of what the AI search tool
    was asked and what it did, and lets a user revisit their own history.
    """
    __tablename__ = "ai_query_logs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[AIQueryStatus] = mapped_column(
        Enum(AIQueryStatus, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False, default=AIQueryStatus.SUCCESS,
    )
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    execution_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_provider: Mapped[str | None] = mapped_column(String(50), nullable=True)

    user: Mapped["User"] = relationship("User")  # type: ignore

    def __repr__(self) -> str:
        return f"<AIQueryLog {self.id} [{self.status}] {self.question[:40]!r}>"
