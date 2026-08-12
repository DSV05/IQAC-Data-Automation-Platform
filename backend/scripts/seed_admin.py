#!/usr/bin/env python3
"""
Seed Script — Run once after migrations to create the first Super Admin.

Usage:
  docker compose exec backend python -m scripts.seed_admin
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_settings
from app.core.security import hash_password
from app.models.user import User, UserRole

settings = get_settings()

ADMIN_EMAIL = os.getenv("SEED_ADMIN_EMAIL", "admin@ganpatuniversity.ac.in")
ADMIN_PASSWORD = os.getenv("SEED_ADMIN_PASSWORD", "Admin@1234")
ADMIN_NAME = os.getenv("SEED_ADMIN_NAME", "IQAC Super Admin")


async def seed():
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        from sqlalchemy import select, func
        result = await session.execute(
            select(func.count()).select_from(User).where(User.role == UserRole.SUPER_ADMIN)
        )
        count = result.scalar_one()
        if count > 0:
            print(f"Super Admin already exists ({count} found). Skipping seed.")
            return

        admin = User(
            email=ADMIN_EMAIL,
            full_name=ADMIN_NAME,
            hashed_password=hash_password(ADMIN_PASSWORD),
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            is_verified=True,
        )
        session.add(admin)
        await session.commit()
        print(f"Super Admin created: {ADMIN_EMAIL}")
        print(f"IMPORTANT: Change the default password immediately after first login!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
