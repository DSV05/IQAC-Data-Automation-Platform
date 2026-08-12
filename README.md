# Update Mode + Inline Edit — File Patch

Fixes two real problems: (1) bulk-updating existing records (e.g. CGPA) via
Excel Upload was impossible — you either got "required fields missing" or
"duplicate detected" — and (2) there was no way to edit a single record
(e.g. one student's CGPA) without a spreadsheet at all.

Drop these into your existing `iqac-platform/` folder, choosing "Replace"
for all 10 — every file here already existed and is being modified; no new
files, no new dependencies, no migration needed.

## No new dependencies, no migration

Everything here reuses existing packages and existing tables. A plain
restart is enough — no `--build`, no `alembic upgrade`.

## Files changed (10)

**Backend (6):**
- `app/utils/column_maps.py` — added a `backlogs` column to the Students template, and a new `NATURAL_KEYS` registry (`students` -> `enrollment_no`, `faculty` -> `employee_id`) that powers Update Mode
- `app/utils/excel_validator.py` — added a `mode` param; in `"update"` mode, only the natural key is required, every other column becomes optional
- `app/repositories/master.py` — added `StudentRepository.get_by_enrollment_year()` (the missing piece — see below)
- `app/utils/db_inserter.py` — students (and faculty) now update-on-match instead of crashing on duplicates; rows with no match in Update Mode are cleanly skipped instead of attempted as broken inserts; new-record inserts are now wrapped in a savepoint so one bad row can't abort the whole batch
- `app/services/upload.py` — threads `mode` through, tracks a `skipped_existing` count, and reports a batch as "partial" (not falsely "completed") when every row was skipped
- `app/api/v1/endpoints/uploads.py` — added a `mode` form field (`"insert"` default, or `"update"`)

**Frontend (4):**
- `services/upload.service.ts` — added the `mode` param
- `components/uploads/UploadResultPanel.tsx` — shows a "Skipped" stat and explains why rows were skipped
- `pages/uploads/UploadsPage.tsx` — added an Insert / Update toggle (only shown for Students and Faculty, the two entities that support it)
- `pages/master/MasterDataPage.tsx` — added a working Edit button per student row, opening a modal to update CGPA, current year, last-semester SGPA, backlogs, active status, and remarks — calling your existing `PUT /master/students/{id}` endpoint (this endpoint already existed; only the UI to reach it was missing)

## What was actually wrong (for your own understanding)

1. The real root cause of both your errors: `StudentRepository` never had
   a `get_by_enrollment_year()` method, so every single Excel upload treated
   every row as brand new — even if that student already existed. Re-uploading
   an existing student crashed with a raw database "duplicate key" error
   (the "duplicate detected" you saw). Faculty already had this method, which
   is why faculty uploads never had this problem — it was specific to Students.
2. Separately, even after fixing that, uploading a CGPA-only file would
   still have failed validation, because the Students template required
   `full_name`, `gender`, `year_of_admission`, etc. to be present in every
   row — Update Mode is what relaxes that, so only `enrollment_no` is required.
3. A related crash risk found and fixed while testing: because the whole
   upload runs in one database transaction, a single bad row (a duplicate,
   or a new student missing a required field) could silently abort every
   other row in the same file, not just that one row. Rows are now
   individually protected against this.

## How to use it

Bulk CGPA update for your 9,243 students:
1. Go to Data Upload -> select Students -> the "Upload Mode" toggle appears
2. Click "Update Existing Records"
3. Prepare a file with just two columns: `enrollment_no` and `cgpa` (column
   name matching is flexible — "Enrollment No", "enrollment_number", etc.
   all map to the same field, same as before)
4. Upload — only students that already exist get updated; only the CGPA
   field changes; nothing else about the record is touched

Editing one student directly:
1. Go to Master Data -> Students
2. Click "Edit" on any row
3. Update CGPA (or current year, SGPA, backlogs, active status, remarks)
4. Save — updates immediately, no file needed

## Scope note

Only Students and Faculty support Update Mode right now, since those are
the two entities with a clear natural key (enrollment number / employee
ID) already established in the codebase. The same pattern can be extended
to other entities (Research, Placements, etc.) if needed later — just say
which one and it can be wired up the same way.

Also worth knowing: bulk-inserting brand-new students via Excel still has a
separate, pre-existing gap — the Students template has no column for
assigning a Program, so new-student rows without a matching Program get
skipped rather than inserted incompletely. This isn't something touched in
this patch (it's unrelated to the CGPA/update problem reported) — flagging
it in case it's run into separately.

## Verified before delivery

- CGPA-only file (just `enrollment_no` + `cgpa`) validated with zero errors
  in Update Mode and correctly updated only that field, leaving name/gender/
  everything else untouched
- Re-uploading a full roster that includes an already-existing student no
  longer crashes — it updates that student instead
- A mixed file (one existing student + one incomplete new student) processes
  the existing student successfully and cleanly skips the incomplete one,
  instead of the whole batch failing
- An Update Mode file referencing an enrollment number that doesn't exist
  is skipped cleanly, not inserted as a broken record
