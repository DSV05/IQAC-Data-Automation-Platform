from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

router = APIRouter()


@router.get("")
async def api_health(db: AsyncSession = Depends(get_db)):
    """
    Deep health check — verifies API + database connectivity.
    Returns 200 if everything is healthy.
    """
    db_ok = False
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if db_ok else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "api": True,
            "database": db_ok,
        },
    }
