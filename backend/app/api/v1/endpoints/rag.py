"""
Module 7 — RAG Chatbot Endpoints
==================================
POST   /api/v1/rag/documents            — upload a PDF, kicks off background ingestion
GET    /api/v1/rag/documents            — list all ingested documents
DELETE /api/v1/rag/documents/{id}       — remove a document and its vectors
POST   /api/v1/rag/chat                 — ask a question, get an answer with citations
GET    /api/v1/rag/chat/history         — current user's past questions
GET    /api/v1/rag/info                 — whether AI is configured, document counts
"""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.permissions import require_permission
from app.db.session import AsyncSessionLocal, get_db
from app.models.rag import RAGChatLog, RAGDocument, RAGDocumentStatus, RAGDocumentType
from app.models.user import User
from app.schemas.rag import (
    RAGChatHistoryItem,
    RAGChatRequest,
    RAGChatResponse,
    RAGDocumentItem,
    RAGInfo,
)
from app.services.rag import RAGChatService, RAGIngestionService
from app.utils import rag_vectorstore

router = APIRouter()
settings = get_settings()

ALLOWED_EXTENSIONS = {".pdf"}


def _enum_value(v) -> str:
    """Handles both a real enum member and a plain string that hasn't been re-hydrated yet."""
    return v.value if hasattr(v, "value") else str(v)


def _document_to_item(doc: RAGDocument) -> RAGDocumentItem:
    return RAGDocumentItem(
        id=doc.id,
        title=doc.title,
        original_filename=doc.original_filename,
        doc_type=_enum_value(doc.doc_type),
        academic_year=doc.academic_year,
        status=_enum_value(doc.status),
        page_count=doc.page_count,
        chunk_count=doc.chunk_count,
        file_size_bytes=doc.file_size_bytes,
        error_message=doc.error_message,
        uploaded_by_name=doc.uploader.full_name if doc.uploader else None,
        created_at=doc.created_at,
    )


async def _run_ingestion(document_id: uuid.UUID) -> None:
    """Runs in a background task with its own DB session (the request's session is long gone)."""
    async with AsyncSessionLocal() as db:
        await RAGIngestionService(db).ingest(document_id)


@router.get("/info", response_model=RAGInfo)
async def get_rag_info(
    current_user: User = Depends(require_permission("rag:chat")),
    db: AsyncSession = Depends(get_db),
):
    total = await db.scalar(select(func.count()).select_from(RAGDocument))
    ready = await db.scalar(
        select(func.count()).select_from(RAGDocument).where(RAGDocument.status == RAGDocumentStatus.READY)
    )
    return RAGInfo(
        ai_configured=settings.ai_configured,
        ai_provider=settings.AI_PROVIDER,
        document_count=total or 0,
        ready_document_count=ready or 0,
    )


@router.post("/documents", response_model=RAGDocumentItem, status_code=status.HTTP_201_CREATED)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    doc_type: str = Form("other"),
    academic_year: str | None = Form(None),
    current_user: User = Depends(require_permission("rag:manage")),
    db: AsyncSession = Depends(get_db),
):
    """
    Uploads a PDF and schedules it for background processing (text extraction,
    chunking, and embedding). The document is created with status='processing'
    immediately; poll GET /documents to see when it becomes 'ready' or 'failed'.
    """
    original_filename = file.filename or "document.pdf"
    ext = Path(original_filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    contents = await file.read()
    if len(contents) > settings.rag_max_file_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds the {settings.RAG_MAX_FILE_SIZE_MB}MB limit.",
        )

    try:
        doc_type_enum = RAGDocumentType(doc_type) if doc_type in {t.value for t in RAGDocumentType} else RAGDocumentType.OTHER
    except Exception:  # noqa: BLE001
        doc_type_enum = RAGDocumentType.OTHER

    os.makedirs(settings.RAG_DOCS_DIR, exist_ok=True)
    stored_filename = f"{uuid.uuid4()}{ext}"
    file_path = Path(settings.RAG_DOCS_DIR) / stored_filename
    with open(file_path, "wb") as f:
        f.write(contents)

    doc = RAGDocument(
        title=title.strip() or original_filename,
        original_filename=original_filename,
        stored_filename=stored_filename,
        doc_type=doc_type_enum,
        academic_year=academic_year,
        status=RAGDocumentStatus.PROCESSING,
        file_size_bytes=len(contents),
        uploaded_by=current_user.id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc, attribute_names=["uploader"])

    background_tasks.add_task(_run_ingestion, doc.id)

    return _document_to_item(doc)


@router.get("/documents", response_model=list[RAGDocumentItem])
async def list_documents(
    current_user: User = Depends(require_permission("rag:chat")),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(RAGDocument).order_by(RAGDocument.created_at.desc())
    result = await db.execute(stmt)
    docs = result.scalars().all()
    for doc in docs:
        await db.refresh(doc, attribute_names=["uploader"])
    return [_document_to_item(d) for d in docs]


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(require_permission("rag:manage")),
    db: AsyncSession = Depends(get_db),
):
    doc = await db.get(RAGDocument, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if doc.vector_ids:
        await rag_vectorstore.delete_ids(doc.vector_ids)

    file_path = Path(settings.RAG_DOCS_DIR) / doc.stored_filename
    if file_path.exists():
        try:
            os.remove(file_path)
        except OSError:
            pass

    await db.delete(doc)
    await db.commit()


@router.post("/chat", response_model=RAGChatResponse)
async def chat(
    payload: RAGChatRequest,
    current_user: User = Depends(require_permission("rag:chat")),
    db: AsyncSession = Depends(get_db),
):
    service = RAGChatService(db)
    result = await service.ask(
        user_id=current_user.id,
        question=payload.question,
        document_id=payload.document_id,
    )
    return RAGChatResponse(**result)


@router.get("/chat/history", response_model=list[RAGChatHistoryItem])
async def chat_history(
    limit: int = 20,
    current_user: User = Depends(require_permission("rag:chat")),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(RAGChatLog)
        .where(RAGChatLog.user_id == current_user.id)
        .order_by(RAGChatLog.created_at.desc())
        .limit(min(limit, 100))
    )
    result = await db.execute(stmt)
    return result.scalars().all()
