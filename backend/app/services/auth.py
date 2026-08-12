"""
Authentication Service
======================
All business logic lives here. Endpoints are thin; they delegate here.
Repository handles DB. Service handles rules and coordination.
"""
import hashlib
import math
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.auth import (
    DepartmentCreate,
    DepartmentRead,
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserRead,
    UserUpdate,
    PaginatedUsers,
)

settings = get_settings()


def _hash_token(token: str) -> str:
    """Store only the hash of refresh tokens — raw tokens never touch the DB."""
    return hashlib.sha256(token.encode()).hexdigest()


class AuthService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    # ── Login / Logout ─────────────────────────────────────────────────────────

    async def login(
        self, data: LoginRequest, request: Request
    ) -> TokenResponse:
        user = await self.repo.get_by_email(data.email)

        # Constant-time comparison — prevents timing attacks on email enumeration
        dummy_hash = "$2b$12$notarealhashatallxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        password_ok = verify_password(
            data.password, user.hashed_password if user else dummy_hash
        )

        if not user or not password_ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account deactivated. Contact your administrator.",
            )

        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)

        refresh_expires = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        await self.repo.store_refresh_token(
            user_id=user.id,
            token_hash=_hash_token(refresh_token),
            expires_at=refresh_expires,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )

        await self.repo.update_last_login(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserRead.model_validate(user),
        )

    async def refresh_access_token(self, raw_refresh_token: str) -> str:
        """Exchange a valid refresh token for a new access token."""
        try:
            payload = decode_token(raw_refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError("Wrong token type")
            user_id = uuid.UUID(payload["sub"])
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token",
            )

        token_record = await self.repo.get_refresh_token(_hash_token(raw_refresh_token))
        if not token_record or not token_record.is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked or expired",
            )

        user = await self.repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or deactivated",
            )

        return create_access_token(user.id)

    async def logout(self, raw_refresh_token: str) -> None:
        await self.repo.revoke_refresh_token(_hash_token(raw_refresh_token))

    # ── Password management ────────────────────────────────────────────────────

    async def change_password(
        self, user: User, current_password: str, new_password: str
    ) -> None:
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )
        await self.repo.update(user, hashed_password=hash_password(new_password))
        await self.repo.revoke_all_user_tokens(user.id)

    async def forgot_password(self, email: str) -> tuple[str, User] | None:
        """
        Generate a reset token.
        Returns (token, user) so the caller can email it.
        Returns None silently if email not found — prevents enumeration.
        """
        user = await self.repo.get_by_email(email)
        if not user or not user.is_active:
            return None

        reset_token = secrets.token_urlsafe(48)
        expires = datetime.now(timezone.utc) + timedelta(hours=2)
        await self.repo.update(
            user,
            reset_token=reset_token,
            reset_token_expires=expires,
        )
        return reset_token, user

    async def reset_password(self, token: str, new_password: str) -> None:
        user = await self.repo.get_by_reset_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token",
            )
        if user.reset_token_expires and user.reset_token_expires < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired. Request a new one.",
            )
        await self.repo.update(
            user,
            hashed_password=hash_password(new_password),
            reset_token=None,
            reset_token_expires=None,
        )
        await self.repo.revoke_all_user_tokens(user.id)

    # ── User management ────────────────────────────────────────────────────────

    async def create_user(self, data: UserCreate, created_by: User) -> UserRead:
        """Only IQAC Admin+ can create users."""
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{data.email}' already exists",
            )

        # Validate department if provided
        if data.department_id:
            dept = await self.repo.get_department_by_id(data.department_id)
            if not dept:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Department not found",
                )

        user = await self.repo.create(
            email=data.email.lower(),
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
            role=data.role,
            department_id=data.department_id,
            is_verified=True,  # Admin-created users are pre-verified
        )
        return UserRead.model_validate(user)

    async def update_user(
        self, user_id: uuid.UUID, data: UserUpdate, updated_by: User
    ) -> UserRead:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        update_data = data.model_dump(exclude_unset=True)
        user = await self.repo.update(user, **update_data)
        return UserRead.model_validate(user)

    async def get_user(self, user_id: uuid.UUID) -> UserRead:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserRead.model_validate(user)

    async def list_users(
        self,
        page: int = 1,
        size: int = 20,
        role: UserRole | None = None,
        department_id: uuid.UUID | None = None,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> PaginatedUsers:
        users, total = await self.repo.list_users(
            page=page, size=size, role=role,
            department_id=department_id, search=search, is_active=is_active
        )
        return PaginatedUsers(
            items=[UserRead.model_validate(u) for u in users],
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total else 0,
        )

    # ── Department management ──────────────────────────────────────────────────

    async def create_department(self, data: DepartmentCreate) -> DepartmentRead:
        existing = await self.repo.get_department_by_code(data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Department with code '{data.code}' already exists",
            )
        dept = await self.repo.create_department(**data.model_dump())
        return DepartmentRead.model_validate(dept)

    async def list_departments(self) -> list[DepartmentRead]:
        depts = await self.repo.list_departments()
        return [DepartmentRead.model_validate(d) for d in depts]
