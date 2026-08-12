"""Research publications, patents, and funded projects."""
import uuid
from datetime import date

from sqlalchemy import (
    Boolean, Date, Enum, Float, ForeignKey,
    Integer, String, Text, ARRAY,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import (
    FundingAgency, IndexingType, PatentStatus, PublicationCategory,
)


class ResearchPublication(BaseModel):
    """
    Journal articles, conference papers, books, book chapters.
    Mapped to NIRF Research, QS/THE citations, NAAC Criterion III.
    """
    __tablename__ = "research_publications"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )

    # Publication details
    title: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[PublicationCategory] = mapped_column(
        Enum(PublicationCategory, values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    journal_conference_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    publication_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    publication_month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    volume: Mapped[str | None] = mapped_column(String(20), nullable=True)
    issue: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pages: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Identifiers
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    isbn_issn: Mapped[str | None] = mapped_column(String(50), nullable=True)
    scopus_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Indexing & impact
    indexing: Mapped[IndexingType] = mapped_column(
        Enum(IndexingType, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=IndexingType.OTHER
    )
    impact_factor: Mapped[float | None] = mapped_column(Float, nullable=True)
    citations: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    h_index_contribution: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Authors (stored as comma-separated string; parsed when needed)
    authors: Mapped[str] = mapped_column(Text, nullable=False)  # "Smith J, Doe A, ..."
    faculty_employee_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # CSV of employee IDs

    # SDG mapping
    sdg_goals: Mapped[str | None] = mapped_column(Text, nullable=True)  # CSV: "3,4,13"

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped["Department"] = relationship("Department")  # type: ignore


class Patent(BaseModel):
    """Patents filed, published, and granted."""
    __tablename__ = "patents"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(Text, nullable=False)
    application_number: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    filing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    grant_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[PatentStatus] = mapped_column(
        Enum(PatentStatus, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=PatentStatus.FILED
    )
    inventors: Mapped[str] = mapped_column(Text, nullable=False)
    faculty_employee_ids: Mapped[str | None] = mapped_column(Text, nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
    patent_office: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped["Department"] = relationship("Department")  # type: ignore


class FundedProject(BaseModel):
    """Externally funded research and consultancy projects."""
    __tablename__ = "funded_projects"

    academic_year: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(Text, nullable=False)
    principal_investigator: Mapped[str] = mapped_column(String(255), nullable=False)
    co_investigators: Mapped[str | None] = mapped_column(Text, nullable=True)
    faculty_employee_ids: Mapped[str | None] = mapped_column(Text, nullable=True)

    funding_agency: Mapped[FundingAgency] = mapped_column(
        Enum(FundingAgency, values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    funding_agency_name: Mapped[str | None] = mapped_column(String(255), nullable=True)  # if OTHER
    scheme: Mapped[str | None] = mapped_column(String(255), nullable=True)

    amount_sanctioned: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    amount_received: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="INR")

    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_ongoing: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    sdg_goals: Mapped[str | None] = mapped_column(Text, nullable=True)
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)

    department: Mapped["Department"] = relationship("Department")  # type: ignore
