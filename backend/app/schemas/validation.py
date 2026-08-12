"""Validation Engine — Pydantic schemas."""
import uuid
from enum import Enum

from pydantic import BaseModel


class IssueSeverity(str, Enum):
    ERROR = "error"       # data integrity problem — must be fixed
    WARNING = "warning"    # missing/incomplete field that affects rankings/reports


class IssueType(str, Enum):
    DUPLICATE = "duplicate"
    ORPHAN_REFERENCE = "orphan_reference"
    INCONSISTENT_REFERENCE = "inconsistent_reference"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_DATE_RANGE = "invalid_date_range"
    LOGICAL_INCONSISTENCY = "logical_inconsistency"


class ValidationIssue(BaseModel):
    entity: str                       # e.g. "faculty", "student"
    record_id: uuid.UUID | None
    academic_year: str | None = None
    severity: IssueSeverity
    issue_type: IssueType
    field: str | None = None
    message: str
    identifier: str | None = None     # human-readable row identifier (employee_id, enrollment_no, etc.)


class ValidationSummary(BaseModel):
    total_records_scanned: int
    total_issues: int
    error_count: int
    warning_count: int
    issues_by_entity: dict[str, int]
    issues_by_type: dict[str, int]


class ValidationReport(BaseModel):
    academic_year: str | None
    summary: ValidationSummary
    issues: list[ValidationIssue]
