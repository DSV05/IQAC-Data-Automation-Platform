"""
Module 4 — Data Validation Engine Endpoints
============================================
GET /api/v1/validation/run      -> run all checks, return JSON report
GET /api/v1/validation/export   -> run all checks, return an Excel workbook
"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import io

from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.user import User
from app.schemas.validation import ValidationReport
from app.services.validation import ValidationEngine
from app.utils.validation_report import generate_validation_report_excel

router = APIRouter()


@router.get("/run", response_model=ValidationReport)
async def run_validation(
    academic_year: str | None = None,
    current_user: User = Depends(require_permission("validation:run")),
    db: AsyncSession = Depends(get_db),
):
    """Run all duplicate/orphan/consistency checks and return the report as JSON."""
    engine = ValidationEngine(db)
    return await engine.run(academic_year=academic_year)


@router.get("/export")
async def export_validation_report(
    academic_year: str | None = None,
    current_user: User = Depends(require_permission("validation:export")),
    db: AsyncSession = Depends(get_db),
):
    """Run all checks and download the results as a styled Excel workbook."""
    engine = ValidationEngine(db)
    report = await engine.run(academic_year=academic_year)
    excel_bytes = generate_validation_report_excel(report)

    filename = f"validation_report_{academic_year or 'all'}.xlsx"
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
