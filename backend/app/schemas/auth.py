import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


# ── Shared ─────────────────────────────────────────────────────────────────────

class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    code: str = Field(..., min_length=2, max_length=20)
    description: str | None = None


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentRead(DepartmentBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── User ───────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.VIEWER
    department_id: uuid.UUID | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserRead(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    department_id: uuid.UUID | None
    department: DepartmentRead | None
    is_active: bool
    is_verified: bool
    last_login_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=255)
    role: UserRole | None = None
    department_id: uuid.UUID | None = None
    is_active: bool | None = None


class UserSummary(BaseModel):
    """Lightweight user object embedded in other responses."""
    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole

    model_config = {"from_attributes": True}


# ── Auth ───────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead


class RefreshRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


# ── Pagination ─────────────────────────────────────────────────────────────────

class PaginatedUsers(BaseModel):
    items: list[UserRead]
    total: int
    page: int
    size: int
    pages: int
