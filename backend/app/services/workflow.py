"""
Module 10 — Workflow & Approvals
===================================
State machine:

  (no row)  --submit-->  SUBMITTED
  SUBMITTED --approve--> APPROVED
  SUBMITTED --reject-->  REJECTED
  REJECTED  --submit-->  SUBMITTED   (version += 1)
  APPROVED  --lock-->    LOCKED      (terminal — no further submissions)

Every transition is appended to WorkflowHistoryEntry, giving a full
version history independent of the current row's state.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import Department, UserRole
from app.models.workflow import WorkflowHistoryEntry, WorkflowStatus, WorkflowSubmission
from app.models.notification import NotificationType
from app.services.notifications import NotificationService


class WorkflowError(Exception):
    """User-facing error — safe to show verbatim in API responses."""


class WorkflowService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_or_create(self, department_id: uuid.UUID, academic_year: str) -> WorkflowSubmission:
        stmt = select(WorkflowSubmission).where(
            WorkflowSubmission.department_id == department_id,
            WorkflowSubmission.academic_year == academic_year,
        )
        result = await self.db.execute(stmt)
        submission = result.scalar_one_or_none()
        if submission:
            return submission

        submission = WorkflowSubmission(
            department_id=department_id, academic_year=academic_year,
            status=WorkflowStatus.DRAFT, version=1,
        )
        self.db.add(submission)
        await self.db.flush()
        return submission

    async def _dept_name(self, department_id: uuid.UUID) -> str:
        result = await self.db.execute(select(Department.name).where(Department.id == department_id))
        return result.scalar_one_or_none() or "your department"

    async def _log(self, submission: WorkflowSubmission, from_status, to_status, actor_id, comments) -> None:
        entry = WorkflowHistoryEntry(
            submission_id=submission.id, from_status=from_status, to_status=to_status,
            version=submission.version, actor_id=actor_id, comments=comments,
        )
        self.db.add(entry)

    async def submit(
        self, actor_id: uuid.UUID, department_id: uuid.UUID, academic_year: str, comments: str | None
    ) -> WorkflowSubmission:
        submission = await self._get_or_create(department_id, academic_year)

        if submission.status == WorkflowStatus.LOCKED:
            raise WorkflowError(
                f"{academic_year} for this department is locked and can no longer be resubmitted."
            )
        if submission.status == WorkflowStatus.SUBMITTED:
            raise WorkflowError("This submission is already awaiting IQAC review.")
        if submission.status == WorkflowStatus.APPROVED:
            raise WorkflowError(
                "This submission has already been approved. Ask an IQAC admin to lock it, "
                "or contact them if it needs to be revised."
            )

        old_status = submission.status
        if old_status == WorkflowStatus.REJECTED:
            submission.version += 1

        submission.status = WorkflowStatus.SUBMITTED
        submission.submitted_by = actor_id
        submission.submitted_at = datetime.now(timezone.utc)

        await self._log(submission, old_status, WorkflowStatus.SUBMITTED, actor_id, comments)

        dept_name = await self._dept_name(department_id)
        await NotificationService(self.db).notify_role_at_least(
            UserRole.IQAC_ADMIN, NotificationType.WORKFLOW_SUBMITTED,
            f"New submission awaiting review: {dept_name}",
            f"{dept_name} submitted their {academic_year} data for IQAC review (version {submission.version}).",
            link="/workflow",
        )

        await self.db.commit()
        await self.db.refresh(submission)
        return submission

    async def review(
        self, actor_id: uuid.UUID, submission_id: uuid.UUID, approve: bool, comments: str | None
    ) -> WorkflowSubmission:
        submission = await self.db.get(WorkflowSubmission, submission_id)
        if not submission:
            raise WorkflowError("Submission not found.")
        if submission.status != WorkflowStatus.SUBMITTED:
            raise WorkflowError("Only submissions awaiting review can be approved or rejected.")

        old_status = submission.status
        submission.status = WorkflowStatus.APPROVED if approve else WorkflowStatus.REJECTED
        submission.reviewed_by = actor_id
        submission.reviewed_at = datetime.now(timezone.utc)
        submission.review_comments = comments

        await self._log(submission, old_status, submission.status, actor_id, comments)

        if submission.submitted_by:
            dept_name = await self._dept_name(submission.department_id)
            if approve:
                notif_type, title = NotificationType.WORKFLOW_APPROVED, f"Submission approved: {dept_name}"
                message = f"Your {submission.academic_year} submission for {dept_name} has been approved."
            else:
                notif_type, title = NotificationType.WORKFLOW_REJECTED, f"Submission rejected: {dept_name}"
                message = f"Your {submission.academic_year} submission for {dept_name} was rejected."
                if comments:
                    message += f" Reviewer comments: {comments}"
            await NotificationService(self.db).notify_user(
                submission.submitted_by, notif_type, title, message, link="/workflow"
            )

        await self.db.commit()
        await self.db.refresh(submission)
        return submission

    async def lock(self, actor_id: uuid.UUID, submission_id: uuid.UUID) -> WorkflowSubmission:
        submission = await self.db.get(WorkflowSubmission, submission_id)
        if not submission:
            raise WorkflowError("Submission not found.")
        if submission.status != WorkflowStatus.APPROVED:
            raise WorkflowError("Only approved submissions can be locked.")

        old_status = submission.status
        submission.status = WorkflowStatus.LOCKED
        submission.locked_by = actor_id
        submission.locked_at = datetime.now(timezone.utc)

        await self._log(submission, old_status, WorkflowStatus.LOCKED, actor_id, None)

        if submission.submitted_by:
            dept_name = await self._dept_name(submission.department_id)
            await NotificationService(self.db).notify_user(
                submission.submitted_by, NotificationType.WORKFLOW_LOCKED,
                f"Submission locked: {dept_name}",
                f"Your {submission.academic_year} submission for {dept_name} has been locked and can no longer be revised.",
                link="/workflow",
            )

        await self.db.commit()
        await self.db.refresh(submission)
        return submission

    async def list_submissions(
        self, department_id: uuid.UUID | None, academic_year: str | None, status: WorkflowStatus | None,
    ) -> list[WorkflowSubmission]:
        stmt = select(WorkflowSubmission).options(
            selectinload(WorkflowSubmission.department),
            selectinload(WorkflowSubmission.submitter),
            selectinload(WorkflowSubmission.reviewer),
            selectinload(WorkflowSubmission.locker),
        )
        if department_id:
            stmt = stmt.where(WorkflowSubmission.department_id == department_id)
        if academic_year:
            stmt = stmt.where(WorkflowSubmission.academic_year == academic_year)
        if status:
            stmt = stmt.where(WorkflowSubmission.status == status)
        stmt = stmt.order_by(WorkflowSubmission.updated_at.desc())

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_submission(self, submission_id: uuid.UUID) -> WorkflowSubmission | None:
        stmt = select(WorkflowSubmission).options(
            selectinload(WorkflowSubmission.department),
            selectinload(WorkflowSubmission.submitter),
            selectinload(WorkflowSubmission.reviewer),
            selectinload(WorkflowSubmission.locker),
        ).where(WorkflowSubmission.id == submission_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_history(self, submission_id: uuid.UUID) -> list[WorkflowHistoryEntry]:
        stmt = (
            select(WorkflowHistoryEntry)
            .options(selectinload(WorkflowHistoryEntry.actor))
            .where(WorkflowHistoryEntry.submission_id == submission_id)
            .order_by(WorkflowHistoryEntry.created_at.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def is_locked(self, department_id: uuid.UUID, academic_year: str) -> bool:
        """
        Convenience helper other modules can call before allowing an edit —
        not wired into any existing endpoint in this delivery, so master-data
        editing behavior elsewhere is unchanged unless you choose to use this.
        """
        stmt = select(WorkflowSubmission.status).where(
            WorkflowSubmission.department_id == department_id,
            WorkflowSubmission.academic_year == academic_year,
        )
        result = await self.db.execute(stmt)
        status = result.scalar_one_or_none()
        return status == WorkflowStatus.LOCKED
