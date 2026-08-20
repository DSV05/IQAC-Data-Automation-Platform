from fastapi import APIRouter
from app.api.v1.endpoints import ai_search, audit, auth, dashboard, excel_templates, health, master, notifications, rag, reports, uploads, validation, workflow

api_router = APIRouter()
api_router.include_router(health.router,          prefix="/health",          tags=["system"])
api_router.include_router(auth.router,             prefix="/auth",            tags=["authentication"])
api_router.include_router(master.router,           prefix="/master",          tags=["master-data"])
api_router.include_router(uploads.router,          prefix="/uploads",         tags=["uploads"])
api_router.include_router(validation.router,       prefix="/validation",      tags=["validation"])
api_router.include_router(dashboard.router,        prefix="/dashboard",       tags=["dashboard"])
api_router.include_router(ai_search.router,        prefix="/ai-search",      tags=["ai-search"])
api_router.include_router(rag.router,              prefix="/rag",             tags=["rag-chatbot"])
api_router.include_router(reports.router,          prefix="/reports",        tags=["reports"])
api_router.include_router(excel_templates.router,  prefix="/excel-templates", tags=["excel-autofill"])
api_router.include_router(workflow.router,         prefix="/workflow",        tags=["workflow"])
api_router.include_router(notifications.router,    prefix="/notifications",  tags=["notifications"])
api_router.include_router(audit.router,            prefix="/audit",          tags=["audit"])
