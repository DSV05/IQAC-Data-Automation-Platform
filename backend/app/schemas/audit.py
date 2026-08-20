import uuid
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    entity_label: Optional[str] = None
    action: str
    changed_by: Optional[uuid.UUID] = None
    changed_by_name: Optional[str] = None
    academic_year: Optional[str] = None
    source: str
    changes: dict[str, Any]
    created_at: datetime


class PaginatedAuditLogs(BaseModel):
    items: list[AuditLogRead]
    total: int
    page: int
    size: int
    pages: int
