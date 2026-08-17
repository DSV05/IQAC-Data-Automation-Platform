# Clear Recent Uploads (failed / processing / all)

## What changed

**Backend**
- `backend/app/repositories/upload.py` — added `delete_by_statuses()` for bulk delete.
- `backend/app/services/upload.py` — added `delete_job()` (single) and `clear_jobs()` (bulk, optionally filtered by status).
- `backend/app/api/v1/endpoints/uploads.py` — new endpoints:
  - `DELETE /api/v1/uploads/{job_id}` — remove one upload record (and its saved file).
  - `DELETE /api/v1/uploads/clear?status=failed,processing` — bulk clear; omit `status` to clear everything.

**Frontend**
- `frontend/src/services/upload.service.ts` — added `deleteJob()` and `clearJobs()`.
- `frontend/src/pages/uploads/UploadsPage.tsx` — Recent Uploads panel now has:
  - "Clear failed/processing (N)" button, shown only when there are stuck jobs.
  - "Clear all" button (asks for confirmation).
  - Per-row ✕ button to remove a single entry.

## Drop-in
Copy these files into your project, preserving paths, replacing the existing ones. No DB migration needed — it only deletes existing `upload_jobs` rows.

## Note on "processing" jobs
Uploads in this pipeline are processed synchronously, so a job stuck at "processing" almost always means the request died mid-flight (server restart, timeout, etc.) rather than something still running in the background — it's safe to clear.
