"""
Upload Service — orchestrates the full upload pipeline.
"""
import math
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.upload import UploadEntityType, UploadJob, UploadStatus
from app.models.user import Department, User
from app.models.student import Program
from app.repositories.upload import UploadRepository
from app.utils.db_inserter import insert_rows
from app.utils.excel_validator import ExcelValidator, RowError
from app.utils.error_report import generate_error_report

settings = get_settings()
logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}


class UploadService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UploadRepository(db)

    async def process_upload(
        self,
        file: UploadFile,
        entity_type: str,
        academic_year: str,
        current_user: User,
        mode: str = "insert",
    ) -> dict:
        # 1. Validate file extension
        filename = file.filename or "upload.xlsx"
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{ext}' not supported. Use .xlsx, .xls, or .csv",
            )

        # 2. Validate entity type
        try:
            entity_enum = UploadEntityType(entity_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown entity type: '{entity_type}'. Valid types: {[e.value for e in UploadEntityType]}",
            )

        if mode not in ("insert", "update"):
            raise HTTPException(status_code=400, detail="mode must be 'insert' or 'update'.")

        # 3. Read file content
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        if len(content) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum: {settings.MAX_UPLOAD_SIZE_MB}MB",
            )

        # 4. Save to disk — ensure directory exists
        upload_dir = Path(settings.UPLOAD_DIR) / entity_type / academic_year
        upload_dir.mkdir(parents=True, exist_ok=True)

        safe_name = f"{uuid.uuid4().hex}_{filename}"
        file_path = upload_dir / safe_name

        with open(file_path, "wb") as f:
            f.write(content)

        logger.info("File saved", path=str(file_path), size=len(content))

        # 5. Create job record
        job = await self.repo.create(
            uploaded_by=current_user.id,
            entity_type=entity_enum,
            academic_year=academic_year,
            original_filename=filename,
            file_path=str(file_path),
            file_size_bytes=len(content),
            status=UploadStatus.PROCESSING,
            started_at=datetime.now(timezone.utc),
        )

        # 6. Validate
        try:
            validator = ExcelValidator(entity_type, academic_year, mode=mode)
            result = validator.validate(str(file_path))
            await self._resolve_relationships(result, entity_type, academic_year)
        except ValueError as e:
            logger.error("Validation failed", error=str(e))
            await self.repo.update_status(
                job, UploadStatus.FAILED,
                error_message=str(e),
                completed_at=datetime.now(timezone.utc),
            )
            raise HTTPException(status_code=422, detail=str(e))
        except Exception as e:
            logger.error("Unexpected validation error", error=str(e))
            await self.repo.update_status(
                job, UploadStatus.FAILED,
                error_message=f"Unexpected error: {str(e)}",
                completed_at=datetime.now(timezone.utc),
            )
            raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

        # 7. Insert valid rows
        inserted = updated = skipped_existing = 0
        db_error: str | None = None

        if result.valid_rows:
            try:
                inserted, updated, skipped_existing = await insert_rows(
                    self.db, entity_type, result.valid_rows, mode=mode, actor=current_user
                )
            except Exception as e:
                logger.error("DB insertion error", error=str(e))
                db_error = str(e)

        # 8. Determine status
        if db_error:
            final_status = UploadStatus.FAILED
        elif result.errors and result.valid_rows:
            final_status = UploadStatus.PARTIAL
        elif result.errors and not result.valid_rows:
            final_status = UploadStatus.FAILED
        elif result.valid_rows and inserted == 0 and updated == 0:
            # Every validated row was skipped (e.g. Update Mode with no matching
            # existing records) — nothing actually happened, so this isn't a
            # clean "completed" even though there were no validation errors.
            final_status = UploadStatus.PARTIAL
        else:
            final_status = UploadStatus.COMPLETED

        error_dicts = [
            {"row": e.row, "field": e.field, "value": str(e.value), "error": e.error}
            for e in result.errors
        ]
        total_skipped = result.skipped_rows + skipped_existing

        await self.repo.update_status(
            job, final_status,
            total_rows=result.total_rows,
            valid_rows=len(result.valid_rows),
            inserted_rows=inserted,
            updated_rows=updated,
            skipped_rows=total_skipped,
            error_rows=len(result.errors),
            validation_errors=error_dicts[:500],
            column_mapping=result.column_mapping,
            completed_at=datetime.now(timezone.utc),
            error_message=db_error,
        )

        logger.info(
            "Upload complete",
            status=final_status.value,
            inserted=inserted,
            updated=updated,
            skipped_existing=skipped_existing,
            errors=len(result.errors),
        )

        return {
            "job_id": str(job.id),
            "status": final_status.value,
            "entity_type": entity_type,
            "academic_year": academic_year,
            "original_filename": filename,
            "mode": mode,
            "total_rows": result.total_rows,
            "inserted_rows": inserted,
            "updated_rows": updated,
            "error_rows": len(result.errors),
            "skipped_rows": total_skipped,
            "skipped_validation": result.skipped_rows,
            "skipped_existing": skipped_existing,
            "errors": error_dicts[:50],
            "has_more_errors": len(result.errors) > 50,
        }

    async def _resolve_relationships(self, result, entity_type: str, academic_year: str) -> None:
        """Resolve spreadsheet department/program names or codes to database IDs.

        These fields are deliberately per-row. This lets a single workbook
        contain multiple departments and gives the operator actionable errors
        instead of silently skipping rows that would violate a foreign key.
        """
        department_entities = {"faculty", "students", "research", "patents", "placements"}
        if entity_type not in department_entities:
            return

        departments = (await self.db.execute(select(Department))).scalars().all()
        departments_by_key = {
            key: department
            for department in departments
            for key in (department.name.strip().casefold(), department.code.strip().casefold())
        }
        programs_by_key: dict[tuple[str, str], Program] = {}
        if entity_type == "students":
            programs = (await self.db.execute(
                select(Program).where(Program.academic_year == academic_year)
            )).scalars().all()
            programs_by_key = {
                (str(program.department_id), key): program
                for program in programs
                for key in (program.name.strip().casefold(), program.code.strip().casefold())
            }

        valid_rows: list[dict] = []
        for row in result.valid_rows:
            row_number = row.get("_row_number", 0)
            row_errors: list[RowError] = []
            is_new = not row.get("_record_id")
            department_value = row.get("department")
            department = departments_by_key.get(str(department_value).strip().casefold()) if department_value else None

            if department_value and not department:
                row_errors.append(RowError(row_number, "department", department_value, "Department name or code was not found"))
            elif is_new and not department:
                row_errors.append(RowError(row_number, "department", department_value or "", "Department is required for a new record"))
            elif department:
                row["department_id"] = department.id

            if entity_type == "students":
                program_value = row.get("program")
                program = (
                    programs_by_key.get((str(department.id), str(program_value).strip().casefold()))
                    if department and program_value else None
                )
                if program_value and department and not program:
                    row_errors.append(RowError(row_number, "program", program_value, "Program name or code was not found for the selected department and academic year"))
                elif is_new and not program:
                    row_errors.append(RowError(row_number, "program", program_value or "", "Program is required for a new student record"))
                elif program:
                    row["program_id"] = program.id

            if row_errors:
                result.errors.extend(row_errors)
                result.skipped_rows += 1
            else:
                valid_rows.append(row)
        result.valid_rows = valid_rows

    async def get_error_report(self, job_id: uuid.UUID) -> tuple[bytes, str]:
        job = await self.repo.get_with_uploader(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Upload job not found")

        errors = [
            RowError(row=e["row"], field=e["field"], value=e["value"], error=e["error"])
            for e in (job.validation_errors or [])
        ]

        report_bytes = generate_error_report(
            entity_type=job.entity_type.value,
            academic_year=job.academic_year,
            filename=job.original_filename,
            total_rows=job.total_rows,
            valid_rows=[],
            errors=errors,
        )
        filename = f"error_report_{job.entity_type.value}_{job.academic_year}_{job.id.hex[:8]}.xlsx"
        return report_bytes, filename

    async def delete_job(self, job_id: uuid.UUID) -> None:
        """Remove a single upload job record (and its saved file, if present)."""
        job = await self.repo.get_with_uploader(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Upload job not found")
        if job.file_path:
            try:
                Path(job.file_path).unlink(missing_ok=True)
            except OSError:
                logger.warning("Could not remove upload file", path=job.file_path)
        await self.repo.delete(job)

    async def clear_jobs(self, statuses: list[str] | None = None) -> int:
        """
        Bulk-remove upload job records.
        statuses=None clears everything; otherwise only jobs whose status is
        in the given list (e.g. ["failed", "processing"]) are removed.
        """
        status_enums = [UploadStatus(s) for s in statuses] if statuses else None
        return await self.repo.delete_by_statuses(status_enums)

    async def list_jobs(self, page=1, size=20, entity_type=None, status_filter=None) -> dict:
        status_enum = UploadStatus(status_filter) if status_filter else None
        jobs, total = await self.repo.list_for_user(
            page=page, size=size,
            entity_type=entity_type,
            status=status_enum,
        )
        return {
            "items": [self._job_summary(j) for j in jobs],
            "total": total, "page": page, "size": size,
            "pages": math.ceil(total / size) if total else 0,
        }

    def _job_summary(self, job: UploadJob) -> dict:
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
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }
