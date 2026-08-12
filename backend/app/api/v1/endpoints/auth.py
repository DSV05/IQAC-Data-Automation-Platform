"""
Authentication + User Management Endpoints
==========================================
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/logout
GET  /api/v1/auth/me
PUT  /api/v1/auth/me/password

GET  /api/v1/auth/users
POST /api/v1/auth/users
GET  /api/v1/auth/users/{id}
PUT  /api/v1/auth/users/{id}

GET  /api/v1/auth/departments
POST /api/v1/auth/departments

POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password
"""
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import CurrentUser
from app.core.permissions import require_permission, require_role
from app.db.session import get_db
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.auth import (
    AccessTokenResponse,
    ChangePasswordRequest,
    DepartmentCreate,
    DepartmentRead,
    ForgotPasswordRequest,
    LoginRequest,
    PaginatedUsers,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserCreate,
    UserRead,
    UserUpdate,
)
from app.services.auth import AuthService
from app.utils.email import send_password_reset_email

router = APIRouter()


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


# -- Auth ----------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
):
    """Authenticate and receive JWT tokens."""
    return await service.login(data, request)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh_token(
    data: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Exchange a refresh token for a new access token."""
    new_access = await service.refresh_access_token(data.refresh_token)
    return AccessTokenResponse(access_token=new_access)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    data: RefreshRequest,
    current_user: CurrentUser,
    service: AuthService = Depends(get_auth_service),
):
    """Revoke the provided refresh token."""
    await service.logout(data.refresh_token)


@router.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUser):
    """Return the currently authenticated user."""
    return current_user


@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser,
    service: AuthService = Depends(get_auth_service),
):
    """Change the current user's password. Revokes all existing sessions."""
    await service.change_password(
        current_user, data.current_password, data.new_password
    )


# -- Password Reset ------------------------------------------------------------

@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    data: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    service: AuthService = Depends(get_auth_service),
):
    """
    Generate a reset token and email it to the user.
    Always returns 204 regardless of whether the email exists, to avoid
    leaking which addresses are registered (user enumeration).
    """
    result = await service.forgot_password(data.email)
    if result:
        token, user = result
        background_tasks.add_task(
            send_password_reset_email,
            to_email=user.email,
            reset_token=token,
            user_name=user.full_name or "",
        )


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    data: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Use the token from the reset email to set a new password."""
    await service.reset_password(data.token, data.new_password)


# -- User Management ----------------------------------------------------------

@router.get("/users", response_model=PaginatedUsers)
async def list_users(
    page: int = 1,
    size: int = 20,
    role: UserRole | None = None,
    search: str | None = None,
    is_active: bool | None = None,
    department_id: uuid.UUID | None = None,
    current_user: User = Depends(require_permission("users:read")),
    service: AuthService = Depends(get_auth_service),
):
    return await service.list_users(
        page=page, size=size, role=role, search=search,
        is_active=is_active, department_id=department_id
    )


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    current_user: User = Depends(require_permission("users:create")),
    service: AuthService = Depends(get_auth_service),
):
    return await service.create_user(data, created_by=current_user)


@router.get("/users/{user_id}", response_model=UserRead)
async def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_permission("users:read")),
    service: AuthService = Depends(get_auth_service),
):
    return await service.get_user(user_id)


@router.put("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: uuid.UUID,
    data: UserUpdate,
    current_user: User = Depends(require_permission("users:update")),
    service: AuthService = Depends(get_auth_service),
):
    return await service.update_user(user_id, data, updated_by=current_user)


# -- Departments ---------------------------------------------------------------

@router.get("/departments", response_model=list[DepartmentRead])
async def list_departments(
    current_user: CurrentUser,
    service: AuthService = Depends(get_auth_service),
):
    return await service.list_departments()


@router.post(
    "/departments",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_department(
    data: DepartmentCreate,
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    service: AuthService = Depends(get_auth_service),
):
    return await service.create_department(data)
