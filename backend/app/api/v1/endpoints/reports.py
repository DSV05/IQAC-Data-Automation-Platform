"""
Module 8 — Report Generator Endpoints
=======================================
GET  /api/v1/reports/types           — available report types
POST /api/v1/reports/generate        — generate & download a report (xlsx or pdf)
GET  /api/v1/reports/history         — past report generations
"""
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.reports import ReportGenerationLog
from app.models.user import User
from app.schemas.reports import ReportHistoryItem, ReportTypeInfo
from app.services.reports import REPORT_TYPE_INFO, ReportService, UnknownReportTypeError

router = APIRouter()

MEDIA_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


@router.get("/types", response_model=list[ReportTypeInfo])
async def get_report_types(
    current_user: User = Depends(require_permission("reports:read")),
):
    return REPORT_TYPE_INFO


@router.post("/generate")
async def generate_report(
    report_type: str = Query(..., description="nirf | naac_ssr | aishe"),
    report_format: str = Query("xlsx", description="xlsx | pdf"),
    academic_year: str | None = Query(None, description="e.g. 2023-24; omit for all years"),
    current_user: User = Depends(require_permission("reports:create")),
    db: AsyncSession = Depends(get_db),
):
    if report_format not in MEDIA_TYPES:
        raise HTTPException(status_code=400, detail="report_format must be 'xlsx' or 'pdf'.")

    service = ReportService(db)
    try:
        file_bytes = await service.generate(
            user_id=current_user.id,
            report_type=report_type,
            report_format=report_format,
            academic_year=academic_year,
        )
    except UnknownReportTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    year_slug = (academic_year or "all-years").replace("/", "-")
    filename = f"{report_type}_{year_slug}_{datetime.now().strftime('%Y%m%d')}.{report_format}"

    return StreamingResponse(
        io.BytesIO(file_bytes),
        media_type=MEDIA_TYPES[report_format],
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/history", response_model=list[ReportHistoryItem])
async def get_report_history(
    limit: int = 20,
    current_user: User = Depends(require_permission("reports:read")),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(ReportGenerationLog)
        .where(ReportGenerationLog.user_id == current_user.id)
        .order_by(ReportGenerationLog.created_at.desc())
        .limit(min(limit, 100))
    )
    result = await db.execute(stmt)
    return result.scalars().all()
