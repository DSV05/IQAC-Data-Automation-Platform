"""
Module 5 — Dashboard Endpoint
==============================
GET /api/v1/dashboard/summary?academic_year=2024-25

Returns everything the dashboard page needs in one call: KPI cards,
department breakdowns, year-over-year trends, and the energy/SDG widgets.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.user import User
from app.services.dashboard import DashboardService

router = APIRouter()


@router.get("/summary", response_model=dict)
async def dashboard_summary(
    academic_year: str = "2024-25",
    current_user: User = Depends(require_permission("dashboard:read")),
    db: AsyncSession = Depends(get_db),
):
    return await DashboardService(db).get_summary(academic_year)
