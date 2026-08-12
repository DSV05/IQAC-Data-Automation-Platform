import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    IQAC_ADMIN = "iqac_admin"
    DEPARTMENT_COORDINATOR = "department_coordinator"
    DATA_ENTRY_OPERATOR = "data_entry_operator"
    VIEWER = "viewer"


class Department(BaseModel):
    """
    University department — used to scope what a coordinator can access.
    """
    __tablename__ = "departments"

    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="department")

    def __repr__(self) -> str:
        return f"<Department {self.code}: {self.name}>"


class User(BaseModel):
    """
    Platform user with role-based access control.
    """
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=UserRole.VIEWER
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Password reset
    reset_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reset_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Last login tracking
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    department: Mapped[Department | None] = relationship(
        "Department", back_populates="users"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} [{self.role}]>"


class RefreshToken(BaseModel):
    """
    Stored refresh tokens — allows server-side revocation.
    """
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)

    user: Mapped[User] = relationship("User")

    @property
    def is_valid(self) -> bool:
        from datetime import timezone
        return (
            self.revoked_at is None
            and self.expires_at > datetime.now(timezone.utc)
        )
