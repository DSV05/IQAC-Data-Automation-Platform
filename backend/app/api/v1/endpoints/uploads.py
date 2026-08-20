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


# ── Download template / current data (unified) ────────────────────────────────

@router.get("/templates/{entity_type}")
async def download_template(
    entity_type: str,
    current_user: CurrentUser,
    request: Request,
    academic_year: Optional[str] = Query(
        None,
        description="If given, the file is pre-filled with all existing records "
                    "for that year (plus a hidden Record ID column) so it can be "
                    "edited and re-uploaded as an update. Omit for a blank template.",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Download an Excel file for a given entity — either a blank template, or
    (when `academic_year` is given) the current data for that year, ready to
    edit and upload straight back.

    Every row carries a "Record ID" in column A. On re-upload: a row whose
    Record ID matches an existing record updates only the cells that
    actually changed; a row with no Record ID (or one that matches nothing)
    is inserted as a brand-new record. Nothing else is touched.

    Accepts optional query params of the form `label_<db_field>=Custom Label`
    (e.g. `?label_impact_factor=IF`) to override the header text shown for
    that column — used by the Master Data "Edit Template" admin feature.
    Only the displayed header changes; the underlying db_field/order is
    untouched, so uploads still map correctly regardless of label overrides.
    """
    import enum
    import io
    from datetime import date, datetime

    import xlsxwriter
    from fastapi import HTTPException

    from app.utils.column_maps import get_column_specs
    from app.utils.db_inserter import _REPO_MAP

    specs = get_column_specs(entity_type)
    if not specs:
        raise HTTPException(status_code=404, detail=f"No template for entity: {entity_type}")

    label_overrides = {
        key[len("label_"):]: value
        for key, value in request.query_params.items()
        if key.startswith("label_") and value
    }

    def to_cell_value(v):
        if v is None:
            return ""
        if isinstance(v, enum.Enum):
            return v.value
        if isinstance(v, bool):
            return "Yes" if v else "No"
        if isinstance(v, (date, datetime)):
            return v.strftime("%d/%m/%Y")
        return v

    existing_rows: list = []
    if academic_year:
        repo_cls = _REPO_MAP.get(entity_type)
        if repo_cls is not None:
            repo = repo_cls(db)
            existing_rows, _ = await repo.list(
                page=1, size=100_000,
                filters=[repo.model.academic_year == academic_year],
            )

    output = io.BytesIO()
    wb = xlsxwriter.Workbook(output, {"in_memory": True})
    ws = wb.add_worksheet(entity_type.title()[:31])

    header_fmt = wb.add_format({
        "bold": True, "bg_color": "#003087", "font_color": "white",
        "border": 1, "align": "center",
    })
    required_fmt = wb.add_format({
        "bold": True, "bg_color": "#FFF9C4", "border": 1, "align": "center",
    })
    id_header_fmt = wb.add_format({
        "bold": True, "bg_color": "#6B7280", "font_color": "white",
        "border": 1, "align": "center",
    })
    id_cell_fmt = wb.add_format({"font_color": "#9CA3AF", "border": 1, "align": "left"})
    data_cell_fmt = wb.add_format({"border": 1})
    note_fmt = wb.add_format({"italic": True, "font_color": "#666666"})
    sample_fmt = wb.add_format({"italic": True, "font_color": "#999999", "border": 1})

    # Column A is always the Record ID — the anchor that makes re-upload an
    # update instead of a duplicate insert. Data columns start at column B.
    ws.write(0, 0, "Record ID", id_header_fmt)
    ws.set_column(0, 0, 38)
    for col_idx, spec in enumerate(specs, start=1):
        label = label_overrides.get(spec.db_field, spec.db_field.replace("_", " ").title())
        if spec.required:
            label += " *"
        fmt = required_fmt if spec.required else header_fmt
        ws.write(0, col_idx, label, fmt)
        ws.set_column(col_idx, col_idx, 20)

    if existing_rows:
        for r, item in enumerate(existing_rows, start=1):
            ws.write(r, 0, str(item.id), id_cell_fmt)
            for col_idx, spec in enumerate(specs, start=1):
                ws.write(r, col_idx, to_cell_value(getattr(item, spec.db_field, None)), data_cell_fmt)
        note_row = len(existing_rows) + 2
        ws.write(note_row, 0,
                 f"↑ {len(existing_rows)} existing record(s) for {academic_year}. "
                 f"Edit any cell above to update that record. Add new rows below "
                 f"(leave Record ID blank) to insert new records. Don't edit "
                 f"Record ID on existing rows.",
                 note_fmt)
    else:
        # No data yet (or blank-template request) — same friendly hints as before.
        ws.write(1, 0, "* Required fields (highlighted in yellow)", note_fmt)
        ws.write(2, 0, "Leave Record ID blank for new rows — it's filled in automatically "
                       "when you download this file again after uploading.", note_fmt)
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
        for col_idx, spec in enumerate(specs, start=1):
            hint = hints.get(spec.db_field, "")
            if hint:
                ws.write(3, col_idx, f"e.g. {hint}", sample_fmt)

    wb.close()

    filename = f"{entity_type}_{academic_year}.xlsx" if academic_year else f"template_{entity_type}.xlsx"
    return Response(
        content=output.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
