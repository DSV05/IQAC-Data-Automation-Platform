"""
Module 11 — Notifications — Scheduled Checks
================================================
Two jobs, both idempotent enough to run repeatedly without spamming:

  run_deadline_reminders(db)
    For every Deadline within its reminder window that hasn't already been
    reminded today, notify the relevant department (or all department
    coordinators + IQAC admins if it's institution-wide), then stamp
    last_reminded_on so it won't fire again today.

  run_missing_data_alerts(db, academic_year)
    For each department, if it has zero Faculty, Student, and Research
    Publication records for the given academic year, notify that
    department that data entry hasn't started yet.

Both are called by the APScheduler job in main.py on an interval
(default 24h — see NOTIFICATIONS_CHECK_INTERVAL_HOURS), and can also be
triggered on demand via POST /api/v1/notifications/run-checks.
"""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.faculty import Faculty
from app.models.notification import Deadline, NotificationType
from app.models.research import ResearchPublication
from app.models.student import Student
from app.models.user import Department, UserRole
from app.services.notifications import NotificationService

logger = get_logger(__name__)


async def run_deadline_reminders(db: AsyncSession) -> int:
    """Returns how many deadlines triggered a reminder this run."""
    today = date.today()
    notifier = NotificationService(db)

    result = await db.execute(select(Deadline))
    deadlines = list(result.scalars().all())

    triggered = 0
    for deadline in deadlines:
        if deadline.last_reminded_on == today:
            continue  # already reminded today

        days_left = (deadline.due_date - today).days
        if days_left < 0 or days_left > deadline.reminder_days_before:
            continue  # not due, or already passed without a final reminder window

        title = f"Deadline approaching: {deadline.title}"
        when = "today" if days_left == 0 else f"in {days_left} day{'s' if days_left != 1 else ''}"
        message = f"\"{deadline.title}\" is due {when} ({deadline.due_date.isoformat()})."
        if deadline.description:
            message += f" {deadline.description}"

        if deadline.department_id:
            await notifier.notify_department(
                deadline.department_id, NotificationType.DEADLINE_REMINDER, title, message,
                link="/workflow",
            )
        else:
            await notifier.notify_role_at_least(
                UserRole.DEPARTMENT_COORDINATOR, NotificationType.DEADLINE_REMINDER, title, message,
                link="/workflow",
            )

        deadline.last_reminded_on = today
        triggered += 1

    await db.commit()
    logger.info("deadline_reminders_checked", triggered=triggered, total=len(deadlines))
    return triggered


async def run_missing_data_alerts(db: AsyncSession, academic_year: str) -> int:
    """Returns how many departments were flagged as having no data for the given year."""
    notifier = NotificationService(db)

    result = await db.execute(select(Department).where(Department.is_active == True))  # noqa: E712
    departments = list(result.scalars().all())

    flagged = 0
    for dept in departments:
        faculty_count = await db.scalar(
            select(func.count()).select_from(Faculty).where(
                Faculty.department_id == dept.id, Faculty.academic_year == academic_year,
            )
        )
        student_count = await db.scalar(
            select(func.count()).select_from(Student).where(
                Student.department_id == dept.id, Student.academic_year == academic_year,
            )
        )
        research_count = await db.scalar(
            select(func.count()).select_from(ResearchPublication).where(
                ResearchPublication.department_id == dept.id, ResearchPublication.academic_year == academic_year,
            )
        )

        if (faculty_count or 0) == 0 and (student_count or 0) == 0 and (research_count or 0) == 0:
            title = f"No data entered yet for {academic_year}"
            message = (
                f"{dept.name} has no faculty, student, or research records for {academic_year} yet. "
                "Please upload or enter data before the submission deadline."
            )
            await notifier.notify_department(dept.id, NotificationType.MISSING_DATA, title, message, link="/uploads")
            flagged += 1

    await db.commit()
    logger.info("missing_data_alerts_checked", flagged=flagged, total=len(departments), academic_year=academic_year)
    return flagged
