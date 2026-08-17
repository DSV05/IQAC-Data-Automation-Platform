"""
Upload Module Endpoints
=======================
POST /api/v1/uploads/              — upload an Excel file
GET  /api/v1/uploads/              — list upload jobs
GET  /api/v1/uploads/{id}          — get job details + errors
GET  /api/v1/uploads/{id}/report   — download Excel error report
GET  /api/v1/uploads/templates/{entity} — download blank template
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentUser
from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.user import User
from app.repositories.upload import UploadRepository
from app.services.upload import UploadService

router = APIRouter()


def get_upload_service(db: AsyncSession = Depends(get_db)) -> UploadService:
    return UploadService(db)


# ── Upload a file ─────────────────────────────────────────────────────────────

@router.post("", status_code=201)
async def upload_file(
    file: UploadFile = File(...),
    entity_type: str = Form(...),
    academic_year: str = Form(...),
    department_id: Optional[uuid.UUID] = Form(None),
    mode: str = Form("insert"),
    current_user: User = Depends(require_permission("uploads:create")),
    service: UploadService = Depends(get_upload_service),
):
    """
    Upload an Excel or CSV file for a given entity type and academic year.
    Returns validation results immediately — no background tasks needed for
    files under 50MB.

    mode="insert" (default): creates new records; existing matches are
    updated with whatever the file provides (unchanged prior behavior).
    mode="update": only the entity's natural key (e.g. enrollment_no) is
    required — every other column becomes optional, so a file containing
    just the key plus a couple of fields (e.g. CGPA) validates and updates
    only those fields on the matching existing record. Rows with no match
    are skipped rather than inserted incomplete.
    """
    return await service.process_upload(
        file=file,
        entity_type=entity_type,
        academic_year=academic_year,
        department_id=department_id,
        current_user=current_user,
        mode=mode,
    )


# ── List jobs ─────────────────────────────────────────────────────────────────

@router.get("")
async def list_upload_jobs(
    page: int = 1,
    size: int = 20,
    entity_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(require_permission("uploads:create")),
    service: UploadService = Depends(get_upload_service),
):
    return await service.list_jobs(page=page, size=size,
                                   entity_type=entity_type, status_filter=status)


# ── Clear jobs (bulk) ─────────────────────────────────────────────────────────
# NOTE: registered before "/{job_id}" so "clear" isn't parsed as a job id.

@router.delete("/clear")
async def clear_upload_jobs(
    status: Optional[str] = Query(
        None,
        description="Comma-separated statuses to clear (e.g. 'failed,processing'). Omit to clear all.",
    ),
    current_user: User = Depends(require_permission("uploads:create")),
    service: UploadService = Depends(get_upload_service),
):
    statuses = [s.strip() for s in status.split(",")] if status else None
    deleted = await service.clear_jobs(statuses)
    return {"deleted": deleted}


# ── Delete a single job ───────────────────────────────────────────────────────

@router.delete("/{job_id}", status_code=204)
async def delete_upload_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_permission("uploads:create")),
    service: UploadService = Depends(get_upload_service),
):
    await service.delete_job(job_id)


# ── Get job details ───────────────────────────────────────────────────────────

@router.get("/{job_id}")
async def get_upload_job(
    job_id: uuid.UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    repo = UploadRepository(db)
    job = await repo.get_with_uploader(job_id)
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Upload job not found")

    return {
        "id": str(job.id),
        "entity_type": job.entity_type.value,
        "academic_year": job.academic_year,
        "original_filename": job.original_filename,
        "file_size_bytes": job.file_size_bytes,
        "status": job.status.value,
        "total_rows": job.total_rows,
        "inserted_rows": job.inserted_rows,
        "updated_rows": job.updated_rows,
        "error_rows": job.error_rows,
        "skipped_rows": job.skipped_rows,
        "column_mapping": job.column_mapping,
        "validation_errors": job.validation_errors or [],
        "error_message": job.error_message,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "uploaded_by": job.uploader.full_name if job.uploader else None,
    }


# ── Download error report ─────────────────────────────────────────────────────

@router.get("/{job_id}/report")
async def download_error_report(
    job_id: uuid.UUID,
    current_user: CurrentUser,
    service: UploadService = Depends(get_upload_service),
):
    report_bytes, filename = await service.get_error_report(job_id)
    return Response(
        content=report_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Download blank template ───────────────────────────────────────────────────

@router.get("/templates/{entity_type}")
async def download_template(
    entity_type: str,
    current_user: CurrentUser,
    request: Request,
):
    """
    Download a blank Excel template with correct column headers.

    Accepts optional query params of the form `label_<db_field>=Custom Label`
    (e.g. `?label_impact_factor=IF`) to override the header text shown for
    that column — used by the Master Data "Edit Template" admin feature.
    Only the displayed header changes; the underlying db_field/order is
    untouched, so uploads still map correctly regardless of label overrides.
    """
    from app.utils.column_maps import get_column_specs
    import xlsxwriter
    import io

    specs = get_column_specs(entity_type)
    if not specs:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"No template for entity: {entity_type}")

    # Pull label_<field>=... overrides from the query string
    label_overrides = {
        key[len("label_"):]: value
        for key, value in request.query_params.items()
        if key.startswith("label_") and value
    }

    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {"in_memory": True})
    ws = wb.add_worksheet(entity_type.title())

    header_fmt = wb.add_format({
        "bold": True, "bg_color": "#003087", "font_color": "white",
        "border": 1, "align": "center",
    })
    required_fmt = wb.add_format({
        "bold": True, "bg_color": "#FFF9C4", "border": 1, "align": "center",
    })
    note_fmt = wb.add_format({"italic": True, "font_color": "#666666"})

    # Headers
    for col_idx, spec in enumerate(specs):
        label = label_overrides.get(spec.db_field, spec.db_field.replace("_", " ").title())
        if spec.required:
            label += " *"
        fmt = required_fmt if spec.required else header_fmt
        ws.write(0, col_idx, label, fmt)
        ws.set_column(col_idx, col_idx, 20)

    # Notes row
    ws.write(1, 0, "* Required fields (highlighted in yellow)", note_fmt)
    ws.write(2, 0, f"academic_year will be set to the selected year automatically", note_fmt)

    # Sample data row hint
    hints = {
        "employee_id": "EMP001", "full_name": "Dr. Rajesh Kumar",
        "gender": "male / female / other",
        "designation": "professor / assistant_professor",
        "qualification": "phd / mtech / mba",
        "employment_type": "permanent / contract / visiting",
        "experience_teaching": "12.5",
        "enrollment_no": "201900001", "current_year": "3",
        "year_of_admission": "2021",
        "category": "general / obc / sc / st",
        "publication_year": "2024", "indexing": "scopus / wos / ugc_care",
        "package_lpa": "6.5",
    }
    sample_fmt = wb.add_format({"italic": True, "font_color": "#999999", "border": 1})
    for col_idx, spec in enumerate(specs):
        hint = hints.get(spec.db_field, "")
        if hint:
            ws.write(3, col_idx, f"e.g. {hint}", sample_fmt)

    wb.close()

    filename = f"template_{entity_type}.xlsx"
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
