"""
Module 6 — AI Natural Language Search
======================================
Turns a plain-English question into a read-only SQL query, runs it
safely against the master data tables, and returns both the generated
SQL and the result rows so the user can verify what actually ran.

Pipeline:
  question -> LLM (LangChain) -> raw SQL -> sql_guard.validate_sql()
            -> execute (read-only, row-capped, timed out) -> AIQueryLog

If no AI provider is configured (no OPENAI_API_KEY and provider is
"openai"), the service returns a clear, actionable error instead of a
Python traceback.
"""
import time
import uuid

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.ai_search import AIQueryLog, AIQueryStatus
from app.utils.schema_context import EXAMPLE_QUESTIONS, build_system_prompt
from app.utils.sql_guard import SQLGuardError, validate_sql

settings = get_settings()


class AISearchError(Exception):
    """User-facing error — safe to show verbatim in the API response."""


def _get_llm():
    """
    Lazily builds the LangChain chat model for the configured provider.
    Imports are done inside the function so the app can start up fine
    even if optional AI packages / credentials aren't fully set up.
    """
    if settings.AI_PROVIDER == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(base_url=settings.OLLAMA_BASE_URL, model=settings.AI_MODEL_OLLAMA, temperature=0)

    # default: openai
    if not settings.OPENAI_API_KEY:
        raise AISearchError(
            "AI Natural Language Search isn't configured yet. "
            "Ask your administrator to set OPENAI_API_KEY (or switch AI_PROVIDER to 'ollama') in the environment."
        )
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(api_key=settings.OPENAI_API_KEY, model=settings.AI_MODEL_OPENAI, temperature=0)


class NLToSQLService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _generate_sql(self, question: str, academic_year: str | None) -> str:
        llm = _get_llm()
        system_prompt = build_system_prompt()
        user_prompt = question.strip()
        if academic_year:
            user_prompt += f"\n(If relevant, scope this to academic_year = '{academic_year}'.)"

        try:
            response = await llm.ainvoke(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]
            )
        except Exception as exc:  # noqa: BLE001 — surfacing provider errors to the user is intentional
            raise AISearchError(f"The AI provider returned an error: {exc}") from exc

        content = response.content if hasattr(response, "content") else str(response)
        if not content or not content.strip():
            raise AISearchError("The AI did not return a response. Try rephrasing your question.")
        return content

    async def _execute(self, sql: str) -> tuple[list[str], list[dict], bool]:
        """Runs the validated SELECT with a statement timeout, returns (columns, rows, truncated)."""
        await self.db.execute(
            text(f"SET LOCAL statement_timeout = {int(settings.AI_QUERY_TIMEOUT_SECONDS * 1000)}")
        )
        result = await self.db.execute(text(sql))
        columns = list(result.keys())
        raw_rows = result.fetchall()
        rows = [dict(zip(columns, row)) for row in raw_rows]

        # JSON-safe conversion for UUIDs, dates, Decimals, etc.
        def _coerce(value):
            if isinstance(value, uuid.UUID):
                return str(value)
            if hasattr(value, "isoformat"):
                return value.isoformat()
            return value

        rows = [{k: _coerce(v) for k, v in row.items()} for row in rows]
        truncated = len(rows) >= settings.AI_SQL_ROW_LIMIT
        return columns, rows, truncated

    async def ask(self, user_id: uuid.UUID, question: str, academic_year: str | None = None) -> dict:
        """
        Full pipeline for one question. Always returns a dict shaped like
        NLQueryResponse (minus `id`, which the caller/log record supplies)
        — even on failure, so the caller can render the generated SQL and
        error together.
        """
        start = time.perf_counter()
        generated_sql: str | None = None
        status = AIQueryStatus.SUCCESS
        error_message: str | None = None
        columns: list[str] = []
        rows: list[dict] = []
        truncated = False

        try:
            raw_sql = await self._generate_sql(question, academic_year)
            generated_sql = validate_sql(raw_sql, settings.AI_SQL_ROW_LIMIT)
        except SQLGuardError as exc:
            status = AIQueryStatus.BLOCKED
            error_message = str(exc)
            # Keep whatever the LLM produced (pre-guard) visible for transparency,
            # if we got that far.
            generated_sql = generated_sql or None
        except AISearchError as exc:
            status = AIQueryStatus.ERROR
            error_message = str(exc)

        if status == AIQueryStatus.SUCCESS and generated_sql:
            try:
                columns, rows, truncated = await self._execute(generated_sql)
            except SQLAlchemyError as exc:
                status = AIQueryStatus.ERROR
                error_message = f"The query failed to execute: {exc.__class__.__name__}. Try rephrasing your question."
                await self.db.rollback()

        execution_ms = round((time.perf_counter() - start) * 1000, 1)

        log = AIQueryLog(
            user_id=user_id,
            question=question,
            generated_sql=generated_sql,
            status=status,
            row_count=len(rows) if status == AIQueryStatus.SUCCESS else None,
            execution_ms=execution_ms,
            error_message=error_message,
            ai_provider=settings.AI_PROVIDER,
        )
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)

        return {
            "id": log.id,
            "question": question,
            "generated_sql": generated_sql,
            "status": status.value,
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "execution_ms": execution_ms,
            "truncated": truncated,
            "explanation": None,
            "error_message": error_message,
            "ai_provider": settings.AI_PROVIDER,
        }


def get_example_questions() -> list[str]:
    return EXAMPLE_QUESTIONS
