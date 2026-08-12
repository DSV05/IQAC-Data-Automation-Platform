"""
Role-Based Access Control
=========================

Role hierarchy (most → least privileged):
  super_admin > iqac_admin > department_coordinator > data_entry_operator > viewer

Each role inherits all permissions of roles below it.
"""
from functools import wraps
from typing import Callable

from fastapi import Depends, HTTPException, status

from app.models.user import User, UserRole


# ── Permission sets per role ───────────────────────────────────────────────────

ROLE_PERMISSIONS: dict[UserRole, set[str]] = {
    UserRole.VIEWER: {
        "dashboard:read",
        "faculty:read",
        "students:read",
        "research:read",
        "placements:read",
        "reports:read",
        "ai:search",
        "validation:read",
        "rag:chat",
    },
    UserRole.DATA_ENTRY_OPERATOR: {
        "faculty:create",
        "faculty:update",
        "students:create",
        "students:update",
        "research:create",
        "research:update",
        "placements:create",
        "placements:update",
        "uploads:create",
        "validation:run",
    },
    UserRole.DEPARTMENT_COORDINATOR: {
        "faculty:delete",
        "students:delete",
        "research:delete",
        "placements:delete",
        "reports:create",
        "reports:export",
        "uploads:approve",
        "workflow:submit",
        "validation:export",
        "rag:manage",
    },
    UserRole.IQAC_ADMIN: {
        "users:read",
        "users:create",
        "users:update",
        "reports:approve",
        "workflow:approve",
        "workflow:lock",
        "audit:read",
        "notifications:manage",
        "master_data:manage",
    },
    UserRole.SUPER_ADMIN: {
        "users:delete",
        "users:manage_roles",
        "departments:manage",
        "system:configure",
        "audit:manage",
        "ai:configure",
    },
}

# Role ordering for hierarchy checks
ROLE_LEVEL: dict[UserRole, int] = {
    UserRole.VIEWER: 0,
    UserRole.DATA_ENTRY_OPERATOR: 1,
    UserRole.DEPARTMENT_COORDINATOR: 2,
    UserRole.IQAC_ADMIN: 3,
    UserRole.SUPER_ADMIN: 4,
}


def get_all_permissions(role: UserRole) -> set[str]:
    """Returns all permissions for a role, including inherited ones from lower roles."""
    level = ROLE_LEVEL[role]
    permissions: set[str] = set()
    for r, perms in ROLE_PERMISSIONS.items():
        if ROLE_LEVEL[r] <= level:
            permissions |= perms
    return permissions


def has_permission(user: User, permission: str) -> bool:
    return permission in get_all_permissions(user.role)


def has_minimum_role(user: User, minimum_role: UserRole) -> bool:
    return ROLE_LEVEL[user.role] >= ROLE_LEVEL[minimum_role]


# ── FastAPI dependency factories ───────────────────────────────────────────────

def require_permission(permission: str) -> Callable:
    """
    FastAPI dependency that checks a specific permission.

    Usage:
        @router.get("/faculty")
        async def list_faculty(
            _: None = Depends(require_permission("faculty:read")),
            current_user: User = Depends(get_current_active_user),
        ):
    """
    from app.api.v1.dependencies import get_current_active_user

    async def _check(current_user: User = Depends(get_current_active_user)) -> User:
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires '{permission}'",
            )
        return current_user

    return _check


def require_role(minimum_role: UserRole) -> Callable:
    """
    FastAPI dependency that checks minimum role level.

    Usage:
        @router.delete("/users/{id}")
        async def delete_user(
            current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
        ):
    """
    from app.api.v1.dependencies import get_current_active_user

    async def _check(current_user: User = Depends(get_current_active_user)) -> User:
        if not has_minimum_role(current_user, minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role '{minimum_role.value}' or higher",
            )
        return current_user

    return _check
