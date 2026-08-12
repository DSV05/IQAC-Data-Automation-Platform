"""
Module 11 — Notifications Endpoints
======================================
GET  /api/v1/notifications                    — list current user's notifications
GET  /api/v1/notifications/unread-count        — badge count for the bell icon
POST /api/v1/notifications/{id}/read           — mark one read
POST /api/v1/notifications/read-all            — mark all read

GET    /api/v1/notifications/deadlines         — list deadlines (any authenticated user)
POST   /api/v1/notifications/deadlines         — create a deadline (iqac_admin+)
DELETE /api/v1/notifications/deadlines/{id}    — remove a deadline (iqac_admin+)
POST   /api/v1/notifications/run-checks        — manually trigger both scheduled checks (iqac_admin+)
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user
from app.core.config import get_settings
from app.core.permissions import has_minimum_role
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.notification import (
    DeadlineCreate,
    DeadlineItem,
    NotificationItem,
    UnreadCountResponse,
)
from app.services.notification_checks import run_deadline_reminders, run_missing_data_alerts
from app.services.notifications import DeadlineNotFoundError, DeadlineService, NotificationService

router = APIRouter()
settings = get_settings()


def _require_iqac_admin(user: User) -> None:
    if not has_minimum_role(user, UserRole.IQAC_ADMIN):
        raise HTTPException(status_code=403, detail="Requires IQAC Admin or higher.")


@router.get("", response_model=list[NotificationItem])
async def list_notifications(
    unread_only: bool = False,
    limit: int = 30,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    return await service.list_for_user(current_user.id, unread_only, limit)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    count = await service.unread_count(current_user.id)
    return UnreadCountResponse(count=count)


@router.post("/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    await service.mark_read(current_user.id, notification_id)


@router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = NotificationService(db)
    await service.mark_all_read(current_user.id)


# -- Deadlines ------------------------------------------------------------

@router.get("/deadlines", response_model=list[DeadlineItem])
async def list_deadlines(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = DeadlineService(db)
    deadlines = await service.list()
    return [
        DeadlineItem(
            id=d.id, title=d.title, description=d.description, academic_year=d.academic_year,
            due_date=d.due_date, department_id=d.department_id,
            department_name=d.department.name if d.department else None,
            reminder_days_before=d.reminder_days_before, last_reminded_on=d.last_reminded_on,
            created_at=d.created_at,
        )
        for d in deadlines
    ]


@router.post("/deadlines", response_model=DeadlineItem, status_code=status.HTTP_201_CREATED)
async def create_deadline(
    payload: DeadlineCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    _require_iqac_admin(current_user)
    service = DeadlineService(db)
    d = await service.create(current_user.id, payload)
    return DeadlineItem(
        id=d.id, title=d.title, description=d.description, academic_year=d.academic_year,
        due_date=d.due_date, department_id=d.department_id,
        department_name=d.department.name if d.department else None,
        reminder_days_before=d.reminder_days_before, last_reminded_on=d.last_reminded_on,
        created_at=d.created_at,
    )


@router.delete("/deadlines/{deadline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deadline(
    deadline_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    _require_iqac_admin(current_user)
    service = DeadlineService(db)
    try:
        await service.delete(deadline_id)
    except DeadlineNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/run-checks")
async def run_checks_now(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Manually triggers both scheduled checks immediately — useful for testing without waiting for the interval."""
    _require_iqac_admin(current_user)
    deadlines_triggered = await run_deadline_reminders(db)
    departments_flagged = await run_missing_data_alerts(db, settings.NOTIFICATIONS_CURRENT_ACADEMIC_YEAR)
    return {
        "deadlines_triggered": deadlines_triggered,
        "departments_flagged_missing_data": departments_flagged,
        "academic_year_checked": settings.NOTIFICATIONS_CURRENT_ACADEMIC_YEAR,
    }
