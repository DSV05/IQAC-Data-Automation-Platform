"""Module 9 — Excel Auto-Fill: uploaded template library and fill audit log."""
import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class ExcelTemplate(BaseModel):
    """
    A blank official template (NIRF/AISHE/NAAC's own Excel format, or any
    other spreadsheet) uploaded once and reused for repeated auto-fills.
    Cells in the template contain {{token}} placeholders that get replaced
    with live DB values — see utils/token_registry.py for the available
    tokens and utils/excel_autofill.py for the substitution engine.
    """
    __tablename__ = "excel_templates"

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(300), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(300), nullable=False)
    sheet_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    uploader: Mapped["User"] = relationship("User")  # type: ignore

    def __repr__(self) -> str:
        return f"<ExcelTemplate {self.title!r}>"


class ExcelFillLog(BaseModel):
    """Audit trail of every auto-fill: which template, which year, what got filled/missed."""
    __tablename__ = "excel_fill_logs"

    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("excel_templates.id", ondelete="SET NULL"), nullable=True, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    academic_year: Mapped[str | None] = mapped_column(String(10), nullable=True)
    tokens_filled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tokens_missing: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    template: Mapped["ExcelTemplate"] = relationship("ExcelTemplate")
    user: Mapped["User"] = relationship("User")  # type: ignore

    def __repr__(self) -> str:
        return f"<ExcelFillLog template={self.template_id} filled={self.tokens_filled}>"
