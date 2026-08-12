from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.db.session import engine

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    setup_logging()
    logger.info("IQAC Platform starting", environment=settings.ENVIRONMENT)

    # Module 11 — periodic notification checks (deadline reminders, missing data alerts).
    # Runs in-process; no extra infrastructure (no Celery/Redis worker needed).
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from app.db.session import AsyncSessionLocal
    from app.services.notification_checks import run_deadline_reminders, run_missing_data_alerts

    async def _run_notification_checks() -> None:
        async with AsyncSessionLocal() as db:
            try:
                await run_deadline_reminders(db)
                await run_missing_data_alerts(db, settings.NOTIFICATIONS_CURRENT_ACADEMIC_YEAR)
            except Exception as exc:  # noqa: BLE001 — a failed check must never crash the app
                logger.error("notification_checks_failed", error=str(exc))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _run_notification_checks,
        "interval",
        hours=settings.NOTIFICATIONS_CHECK_INTERVAL_HOURS,
        id="notification_checks",
    )
    scheduler.start()

    yield

    scheduler.shutdown(wait=False)
    await engine.dispose()
    logger.info("IQAC Platform shut down cleanly")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Centralized data automation platform for IQAC, Ganpat University",
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
        openapi_url="/api/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── Middleware ──────────────────────────────────────────────────────────
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ─────────────────────────────────────────────────────────────
    from app.api.v1.router import api_router
    app.include_router(api_router, prefix="/api/v1")

    # ── Health check (no auth required) ─────────────────────────────────────
    @app.get("/health", tags=["system"], include_in_schema=False)
    async def health_check():
        return JSONResponse({"status": "ok", "version": settings.APP_VERSION})

    return app


app = create_app()
