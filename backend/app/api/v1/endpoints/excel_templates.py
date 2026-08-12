"""
Module 9 — Excel Auto-Fill Endpoints
======================================
GET    /api/v1/excel-templates/tokens          — reference list of available {{tokens}}
POST   /api/v1/excel-templates                 — upload a blank official template
GET    /api/v1/excel-templates                 — list uploaded templates
DELETE /api/v1/excel-templates/{id}            — remove a template
POST   /api/v1/excel-templates/{id}/fill       — fill the template with live data & download
GET    /api/v1/excel-templates/fill-history    — past fill operations
"""
import io
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import uuid as uuid_lib

from app.core.config import get_settings
from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.excel_template import ExcelFillLog, ExcelTemplate
from app.models.user import User
from app.schemas.excel_template import (
    ExcelTemplateItem,
    FillHistoryItem,
    FillRequest,
    TokenInfo,
)
from app.services.excel_autofill_service import (
    ExcelFillService,
    ExcelTemplateService,
    TemplateNotFoundError,
)
from app.utils.excel_autofill import ExcelAutoFillError
from app.utils.token_registry import build_token_registry, describe_tokens

router = APIRouter()
settings = get_settings()

ALLOWED_EXTENSIONS = {".xlsx"}


def _template_to_item(t: ExcelTemplate) -> ExcelTemplateItem:
    return ExcelTemplateItem(
        id=t.id,
        title=t.title,
        original_filename=t.original_filename,
        sheet_count=t.sheet_count,
        token_count=t.token_count,
        file_size_bytes=t.file_size_bytes,
        uploaded_by_name=t.uploader.full_name if t.uploader else None,
        created_at=t.created_at,
    )


@router.get("/tokens", response_model=list[TokenInfo])
async def get_available_tokens(
    academic_year: str | None = None,
    current_user: User = Depends(require_permission("reports:read")),
    db: AsyncSession = Depends(get_db),
):
    """Reference list of every {{token}} available for use inside an uploaded template."""
    tokens = await build_token_registry(db, academic_year)
    return describe_tokens(tokens)


@router.post("", response_model=ExcelTemplateItem, status_code=status.HTTP_201_CREATED)
async def upload_template(
    file: UploadFile = File(...),
    title: str = Form(...),
    current_user: User = Depends(require_permission("reports:create")),
    db: AsyncSession = Depends(get_db),
):
    original_filename = file.filename or "template.xlsx"
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

    contents = await file.read()
    if len(contents) > settings.rag_max_file_bytes:  # reuse the same 50MB cap as RAG uploads
        raise HTTPException(status_code=400, detail="File is too large.")

    service = ExcelTemplateService(db)
    try:
        template = await service.upload(current_user.id, title, original_filename, contents)
    except ExcelAutoFillError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _template_to_item(template)


@router.get("", response_model=list[ExcelTemplateItem])
async def list_templates(
    current_user: User = Depends(require_permission("reports:read")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ExcelTemplate).order_by(ExcelTemplate.created_at.desc())
    result = await db.execute(stmt)
    templates = result.scalars().all()
    for t in templates:
        await db.refresh(t, attribute_names=["uploader"])
    return [_template_to_item(t) for t in templates]


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: uuid_lib.UUID,
    current_user: User = Depends(require_permission("reports:create")),
    db: AsyncSession = Depends(get_db),
):
    service = ExcelTemplateService(db)
    try:
        await service.delete(template_id)
    except TemplateNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{template_id}/fill")
async def fill_template_endpoint(
    template_id: uuid_lib.UUID,
    payload: FillRequest,
    current_user: User = Depends(require_permission("reports:export")),
    db: AsyncSession = Depends(get_db),
):
    service = ExcelFillService(db)
    try:
        file_bytes, filename = await service.fill(current_user.id, template_id, payload.academic_year)
    except TemplateNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ExcelAutoFillError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/fill-history", response_model=list[FillHistoryItem])
async def get_fill_history(
    limit: int = 20,
    current_user: User = Depends(require_permission("reports:read")),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ExcelFillLog)
        .where(ExcelFillLog.user_id == current_user.id)
        .order_by(ExcelFillLog.created_at.desc())
        .limit(min(limit, 100))
    )
    result = await db.execute(stmt)
    return result.scalars().all()
