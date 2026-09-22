import asyncio
from logging.config import fileConfig
from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from app.core.config import get_settings
from app.db.session import Base

# Import ALL models so Alembic autogenerate can detect them
from app.models.user import User, Department, RefreshToken
from app.models.faculty import Faculty
from app.models.student import Program, Student
from app.models.research import ResearchPublication, Patent, FundedProject
from app.models.placement import Placement, HigherStudy
from app.models.institutional import Infrastructure, Budget, MoU, Event
from app.models.green import EnergyConsumption, WaterConsumption, WasteManagement, GreenInitiative
from app.models.awards import Award, Accreditation, Consultancy, SDGActivity
from app.models.upload import UploadJob
from app.models.ai_search import AIQueryLog
from app.models.rag import RAGDocument, RAGChatLog
from app.models.reports import ReportGenerationLog
from app.models.excel_template import ExcelTemplate, ExcelFillLog
from app.models.workflow import WorkflowSubmission, WorkflowHistoryEntry
from app.models.notification import Notification, Deadline
from app.models.audit import AuditLog
from app.models.custom_column import CustomColumnDef

config = context.config
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.", poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
