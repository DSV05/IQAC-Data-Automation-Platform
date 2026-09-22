"""
Custom Columns Endpoints
========================
Lets an IQAC Admin add a brand-new column to any Data Category from the
Master Data "Edit Template" modal. Once added, the column appears as an
extra header in that entity's downloaded Excel template (see
uploads.py::download_template) so operators can start filling it in.

GET    /api/v1/custom-columns/{entity_type}            — list columns (any authenticated user)
POST   /api/v1/custom-columns/{entity_type}             — add a column (iqac_admin+)
DELETE /api/v1/custom-columns/{entity_type}/{column_id} — remove a column (iqac_admin+)
"""
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_active_user
from app.core.permissions import has_minimum_role
from app.db.session import get_db
from app.models.custom_column import CustomColumnDef
from app.models.user import User, UserRole
from app.schemas.custom_column import CustomColumnCreate, CustomColumnItem

router = APIRouter()


def _require_iqac_admin(user: User) -> None:
    if not has_minimum_role(user, UserRole.IQAC_ADMIN):
        raise HTTPException(status_code=403, detail="Requires IQAC Admin or higher.")


def _slugify(label: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", label.strip().lower()).strip("_")
    return f"custom_{key}" if key else "custom_field"


@router.get("/{entity_type}", response_model=list[CustomColumnItem])
async def list_custom_columns(
    entity_type: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CustomColumnDef)
        .where(CustomColumnDef.entity_type == entity_type)
        .order_by(CustomColumnDef.created_at)
    )
    return result.scalars().all()


@router.post("/{entity_type}", response_model=CustomColumnItem, status_code=status.HTTP_201_CREATED)
async def add_custom_column(
    entity_type: str,
    payload: CustomColumnCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    _require_iqac_admin(current_user)

    label = payload.label.strip()
    if not label:
        raise HTTPException(status_code=422, detail="Column label cannot be empty.")

    base_key = _slugify(label)
    field_key = base_key
    existing_keys = {
        row.field_key for row in (
            await db.execute(
                select(CustomColumnDef.field_key).where(CustomColumnDef.entity_type == entity_type)
            )
        ).all()
    }
    suffix = 2
    while field_key in existing_keys:
        field_key = f"{base_key}_{suffix}"
        suffix += 1

    column = CustomColumnDef(
        entity_type=entity_type,
        field_key=field_key,
        label=label,
        created_by=current_user.id,
    )
    db.add(column)
    await db.commit()
    await db.refresh(column)
    return column


@router.delete("/{entity_type}/{column_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_custom_column(
    entity_type: str,
    column_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    _require_iqac_admin(current_user)
    await db.execute(
        delete(CustomColumnDef).where(
            CustomColumnDef.id == column_id,
            CustomColumnDef.entity_type == entity_type,
        )
    )
    await db.commit()
