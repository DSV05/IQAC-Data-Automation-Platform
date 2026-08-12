from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    APP_NAME: str = "IQAC Data Automation Platform"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://iqac_user:iqac_secret@localhost:5432/iqac_db"

    # Security
    SECRET_KEY: str = "changeme"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173"

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    # Frontend (used to build links inside emails)
    FRONTEND_URL: str = "http://localhost:5173"

    # Email / SMTP (optional -- if SMTP_HOST is blank, emails are logged
    # to the console instead of sent, so local dev works without a mail server)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_USE_TLS: bool = True
    EMAILS_FROM: str = "iqac@ganpatuniversity.ac.in"
    EMAILS_FROM_NAME: str = "Ganpat University IQAC Platform"

    @property
    def smtp_configured(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI (optional)
    OPENAI_API_KEY: str = ""
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # AI Natural Language Search (Module 6)
    AI_PROVIDER: str = "openai"          # "openai" or "ollama"
    AI_MODEL_OPENAI: str = "gpt-4o-mini"
    AI_MODEL_OLLAMA: str = "llama3.1"
    AI_SQL_ROW_LIMIT: int = 500          # hard cap on rows returned per query
    AI_QUERY_TIMEOUT_SECONDS: int = 15   # DB statement timeout for generated SQL

    @property
    def ai_configured(self) -> bool:
        if self.AI_PROVIDER == "openai":
            return bool(self.OPENAI_API_KEY)
        return bool(self.OLLAMA_BASE_URL)

    # RAG Chatbot (Module 7)
    RAG_EMBEDDING_MODEL_OPENAI: str = "text-embedding-3-small"
    RAG_EMBEDDING_MODEL_OLLAMA: str = "nomic-embed-text"
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 150
    RAG_TOP_K: int = 5
    RAG_MAX_FILE_SIZE_MB: int = 50
    RAG_INDEX_DIR: str = "/app/uploads/rag_index"
    RAG_DOCS_DIR: str = "/app/uploads/rag_docs"

    @property
    def rag_max_file_bytes(self) -> int:
        return self.RAG_MAX_FILE_SIZE_MB * 1024 * 1024

    # Excel Auto-Fill (Module 9)
    EXCEL_TEMPLATE_DIR: str = "/app/uploads/excel_templates"

    # Notifications (Module 11)
    NOTIFICATIONS_CHECK_INTERVAL_HOURS: int = 24
    # Update this each academic year — used by the missing-data-alert job to
    # know which year's records to check for. Not auto-detected on purpose:
    # academic year boundaries vary by institution and shouldn't be guessed.
    NOTIFICATIONS_CURRENT_ACADEMIC_YEAR: str = "2023-24"



    # File uploads
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_DIR: str = "/app/uploads"

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
