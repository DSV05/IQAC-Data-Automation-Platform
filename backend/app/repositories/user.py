import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import Department, RefreshToken, User, UserRole


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── User queries ───────────────────────────────────────────────────────────

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.department))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.department))
            .where(func.lower(User.email) == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_reset_token(self, token: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.reset_token == token)
        )
        return result.scalar_one_or_none()

    async def list_users(
        self,
        page: int = 1,
        size: int = 20,
        role: UserRole | None = None,
        department_id: uuid.UUID | None = None,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[User], int]:
        query = select(User).options(selectinload(User.department))
        count_query = select(func.count()).select_from(User)

        filters = []
        if role:
            filters.append(User.role == role)
        if department_id:
            filters.append(User.department_id == department_id)
        if is_active is not None:
            filters.append(User.is_active == is_active)
        if search:
            pattern = f"%{search}%"
            filters.append(
                or_(
                    User.full_name.ilike(pattern),
                    User.email.ilike(pattern),
                )
            )

        if filters:
            from sqlalchemy import and_
            query = query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        total = (await self.db.execute(count_query)).scalar_one()
        offset = (page - 1) * size
        users_result = await self.db.execute(
            query.order_by(User.created_at.desc()).offset(offset).limit(size)
        )
        return list(users_result.scalars().all()), total

    async def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user, ["department"])
        return user

    async def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            setattr(user, key, value)
        await self.db.flush()
        await self.db.refresh(user, ["department"])
        return user

    async def update_last_login(self, user: User) -> None:
        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()

    # ── Refresh token management ───────────────────────────────────────────────

    async def store_refresh_token(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshToken:
        rt = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
        self.db.add(rt)
        await self.db.flush()
        return rt

    async def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_hash: str) -> None:
        rt = await self.get_refresh_token(token_hash)
        if rt:
            rt.revoked_at = datetime.now(timezone.utc)
            await self.db.flush()

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> None:
        """Used on password change or account deactivation."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        tokens = result.scalars().all()
        now = datetime.now(timezone.utc)
        for token in tokens:
            token.revoked_at = now
        await self.db.flush()

    # ── Department queries ─────────────────────────────────────────────────────

    async def get_department_by_id(self, dept_id: uuid.UUID) -> Department | None:
        result = await self.db.execute(
            select(Department).where(Department.id == dept_id)
        )
        return result.scalar_one_or_none()

    async def list_departments(self) -> list[Department]:
        result = await self.db.execute(
            select(Department).where(Department.is_active == True).order_by(Department.name)
        )
        return list(result.scalars().all())

    async def create_department(self, **kwargs) -> Department:
        dept = Department(**kwargs)
        self.db.add(dept)
        await self.db.flush()
        return dept

    async def get_department_by_code(self, code: str) -> Department | None:
        result = await self.db.execute(
            select(Department).where(func.upper(Department.code) == code.upper())
        )
        return result.scalar_one_or_none()
