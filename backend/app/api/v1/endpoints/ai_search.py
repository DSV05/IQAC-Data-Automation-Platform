"""
Module 6 — AI Natural Language Search Endpoints
=================================================
POST /api/v1/ai-search/query    -> ask a question, get SQL + results
GET  /api/v1/ai-search/history  -> the current user's past queries
GET  /api/v1/ai-search/info     -> whether AI is configured, allowed tables, example questions
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.permissions import require_permission
from app.db.session import get_db
from app.models.ai_search import AIQueryLog
from app.models.user import User
from app.schemas.ai_search import (
    AISchemaInfo,
    AIQueryHistoryItem,
    NLQueryRequest,
    NLQueryResponse,
)
from app.services.ai_search import NLToSQLService, get_example_questions
from app.utils.sql_guard import ALLOWED_TABLES

router = APIRouter()
settings = get_settings()


@router.get("/info", response_model=AISchemaInfo)
async def get_ai_search_info(
    current_user: User = Depends(require_permission("ai:search")),
):
    """Tells the frontend whether AI search is usable right now, and what it can search."""
    return AISchemaInfo(
        ai_configured=settings.ai_configured,
        ai_provider=settings.AI_PROVIDER,
        tables=sorted(ALLOWED_TABLES),
        example_questions=get_example_questions(),
    )


@router.post("/query", response_model=NLQueryResponse)
async def ask_question(
    payload: NLQueryRequest,
    current_user: User = Depends(require_permission("ai:search")),
    db: AsyncSession = Depends(get_db),
):
    """
    Converts a natural-language question into read-only SQL, runs it,
    and returns the generated SQL alongside the result rows. Every
    request is logged (question, SQL, outcome) for audit purposes.
    """
    service = NLToSQLService(db)
    result = await service.ask(
        user_id=current_user.id,
        question=payload.question,
        academic_year=payload.academic_year,
    )
    return NLQueryResponse(**result)


@router.get("/history", response_model=list[AIQueryHistoryItem])
async def get_query_history(
    limit: int = 20,
    current_user: User = Depends(require_permission("ai:search")),
    db: AsyncSession = Depends(get_db),
):
    """Returns the current user's most recent AI search queries, newest first."""
    stmt = (
        select(AIQueryLog)
        .where(AIQueryLog.user_id == current_user.id)
        .order_by(AIQueryLog.created_at.desc())
        .limit(min(limit, 100))
    )
    result = await db.execute(stmt)
    return result.scalars().all()
