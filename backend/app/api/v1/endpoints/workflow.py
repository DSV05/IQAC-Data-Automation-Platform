"""
Module 10 — Workflow & Approvals Endpoints
=============================================
POST /api/v1/workflow/submissions/submit          — submit or resubmit a department's data
GET  /api/v1/workflow/submissions                 — list (scoped to own dept unless reviewer)
GET  /api/v1/workflow/submissions/{id}            — detail
GET  /api/v1/workflow/submissions/{id}/history     — version history
POST /api/v1/workflow/submissions/{id}/review      — approve or reject
POST /api/v1/workflow/submissions/{id}/lock        — lock an approved submission

Visibility rule: a department_coordinator (or lower) only ever sees their
own department's submissions. Anyone with `workflow:approve` (iqac_admin+)
can see and filter across all departments — that's the review queue.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user
from app.core.permissions import has_permission
from app.db.session import get_db
from app.models.user import User
from app.models.workflow import WorkflowStatus
from app.schemas.workflow import (
    HistoryItem,
    ReviewRequest,
    SubmissionItem,
    SubmitRequest,
    WorkflowStatusSchema,
)
from app.services.workflow import WorkflowError, WorkflowService

router = APIRouter()


def _submission_to_item(s) -> SubmissionItem:
    return SubmissionItem(
        id=s.id,
        department_id=s.department_id,
        department_name=s.department.name if s.department else "Unknown",
        academic_year=s.academic_year,
        status=s.status.value,
        version=s.version,
        submitted_by_name=s.submitter.full_name if s.submitter else None,
        submitted_at=s.submitted_at,
        reviewed_by_name=s.reviewer.full_name if s.reviewer else None,
        reviewed_at=s.reviewed_at,
        review_comments=s.review_comments,
        locked_by_name=s.locker.full_name if s.locker else None,
        locked_at=s.locked_at,
        created_at=s.created_at,
    )


def _can_review(user: User) -> bool:
    return has_permission(user, "workflow:approve")


def _assert_can_view(user: User, department_id: uuid.UUID) -> None:
    if _can_review(user):
        return
    if user.department_id != department_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view submissions for your own department.",
        )


@router.post("/submissions/submit", response_model=SubmissionItem)
async def submit_for_review(
    payload: SubmitRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not has_permission(current_user, "workflow:submit"):
        raise HTTPException(status_code=403, detail="Permission denied: requires 'workflow:submit'")

    if not _can_review(current_user) and current_user.department_id != payload.department_id:
        raise HTTPException(
            status_code=403,
            detail="You can only submit data for your own department.",
        )

    service = WorkflowService(db)
    try:
        submission = await service.submit(
            actor_id=current_user.id,
            department_id=payload.department_id,
            academic_year=payload.academic_year,
            comments=payload.comments,
        )
    except WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    full = await service.get_submission(submission.id)
    return _submission_to_item(full)


@router.get("/submissions", response_model=list[SubmissionItem])
async def list_submissions(
    department_id: uuid.UUID | None = Query(None),
    academic_year: str | None = Query(None),
    status_filter: WorkflowStatusSchema | None = Query(None, alias="status"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)

    # Non-reviewers only ever see their own department, regardless of what they ask for.
    effective_department_id = department_id
    if not _can_review(current_user):
        effective_department_id = current_user.department_id

    status_enum = WorkflowStatus(status_filter.value) if status_filter else None
    submissions = await service.list_submissions(effective_department_id, academic_year, status_enum)
    return [_submission_to_item(s) for s in submissions]


@router.get("/submissions/{submission_id}", response_model=SubmissionItem)
async def get_submission(
    submission_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    submission = await service.get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")

    _assert_can_view(current_user, submission.department_id)
    return _submission_to_item(submission)


@router.get("/submissions/{submission_id}/history", response_model=list[HistoryItem])
async def get_submission_history(
    submission_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = WorkflowService(db)
    submission = await service.get_submission(submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")

    _assert_can_view(current_user, submission.department_id)

    history = await service.get_history(submission_id)
    return [
        HistoryItem(
            id=h.id, from_status=h.from_status.value if h.from_status else None,
            to_status=h.to_status.value, version=h.version,
            actor_name=h.actor.full_name if h.actor else None,
            comments=h.comments, created_at=h.created_at,
        )
        for h in history
    ]


@router.post("/submissions/{submission_id}/review", response_model=SubmissionItem)
async def review_submission(
    submission_id: uuid.UUID,
    payload: ReviewRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not has_permission(current_user, "workflow:approve"):
        raise HTTPException(status_code=403, detail="Permission denied: requires 'workflow:approve'")

    service = WorkflowService(db)
    try:
        await service.review(
            actor_id=current_user.id,
            submission_id=submission_id,
            approve=(payload.decision.value == "approve"),
            comments=payload.comments,
        )
    except WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    full = await service.get_submission(submission_id)
    return _submission_to_item(full)


@router.post("/submissions/{submission_id}/lock", response_model=SubmissionItem)
async def lock_submission(
    submission_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not has_permission(current_user, "workflow:lock"):
        raise HTTPException(status_code=403, detail="Permission denied: requires 'workflow:lock'")

    service = WorkflowService(db)
    try:
        await service.lock(actor_id=current_user.id, submission_id=submission_id)
    except WorkflowError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    full = await service.get_submission(submission_id)
    return _submission_to_item(full)
