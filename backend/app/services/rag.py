"""
Module 7 — RAG Chatbot
=======================
Two pipelines:

  Ingestion:  PDF -> per-page text -> chunks -> embed -> FAISS index
  Chat:       question -> embed -> similarity search -> LLM answer w/ citations

Both are careful to fail into a clear, stored error rather than crash —
ingestion marks the document `failed` with a reason; chat logs an
`error` status with a user-facing message.
"""
import time
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.rag import RAGChatLog, RAGChatStatus, RAGDocument, RAGDocumentStatus
from app.utils import rag_vectorstore
from app.utils.llm_provider import LLMProviderError, get_chat_llm
from app.utils.pdf_extractor import PDFExtractionError, extract_pages

settings = get_settings()
logger = get_logger(__name__)


class RAGIngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ingest(self, document_id: uuid.UUID) -> None:
        """
        Runs the full pipeline for one already-saved-to-disk document row.
        Meant to be scheduled as a background task right after upload —
        it commits its own transaction so it can run after the request
        that created it has already returned.
        """
        doc = await self.db.get(RAGDocument, document_id)
        if not doc:
            logger.warning("rag_ingest_missing_document", document_id=str(document_id))
            return

        file_path = Path(settings.RAG_DOCS_DIR) / doc.stored_filename
        try:
            pages = extract_pages(file_path)
            chunks = self._split_into_chunks(pages, doc)
            if not chunks:
                raise PDFExtractionError("No usable text chunks were produced from this PDF.")

            ids = await rag_vectorstore.add_documents(chunks)

            doc.page_count = len(pages)
            doc.chunk_count = len(chunks)
            doc.vector_ids = ids
            doc.status = RAGDocumentStatus.READY
            doc.error_message = None

        except PDFExtractionError as exc:
            doc.status = RAGDocumentStatus.FAILED
            doc.error_message = str(exc)
        except Exception as exc:  # noqa: BLE001 — ingestion must never crash the worker
            logger.error("rag_ingest_failed", document_id=str(document_id), error=str(exc))
            doc.status = RAGDocumentStatus.FAILED
            doc.error_message = f"Unexpected error while processing this document: {exc}"

        await self.db.commit()

    def _split_into_chunks(self, pages: list[str], doc: RAGDocument) -> list:
        from langchain_core.documents import Document
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.RAG_CHUNK_SIZE,
            chunk_overlap=settings.RAG_CHUNK_OVERLAP,
        )

        chunks: list[Document] = []
        for page_num, page_text in enumerate(pages, start=1):
            if not page_text.strip():
                continue
            for piece in splitter.split_text(page_text):
                if not piece.strip():
                    continue
                chunks.append(
                    Document(
                        page_content=piece,
                        metadata={
                            "document_id": str(doc.id),
                            "title": doc.title,
                            "filename": doc.original_filename,
                            "doc_type": doc.doc_type.value,
                            "page": page_num,
                        },
                    )
                )
        return chunks


class RAGChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def ask(
        self,
        user_id: uuid.UUID,
        question: str,
        document_id: uuid.UUID | None = None,
    ) -> dict:
        start = time.perf_counter()
        status = RAGChatStatus.SUCCESS
        answer: str | None = None
        sources: list[dict] = []
        error_message: str | None = None

        try:
            results = await rag_vectorstore.similarity_search(
                question, k=settings.RAG_TOP_K,
                document_id=str(document_id) if document_id else None,
            )
            if not results:
                answer = (
                    "I don't have any indexed documents to search yet (or none matched this "
                    "question). Upload a NAAC SSR, Annual Report, or similar PDF first, then ask again."
                )
            else:
                context_blocks = []
                for i, (doc, score) in enumerate(results, start=1):
                    context_blocks.append(
                        f"[Source {i}] ({doc.metadata.get('title')}, page {doc.metadata.get('page')}):\n"
                        f"{doc.page_content}"
                    )
                    sources.append({
                        "document_id": doc.metadata.get("document_id"),
                        "title": doc.metadata.get("title"),
                        "filename": doc.metadata.get("filename"),
                        "page": doc.metadata.get("page"),
                        "snippet": doc.page_content[:300],
                        "score": float(score),
                    })
                context = "\n\n".join(context_blocks)

                llm = get_chat_llm(temperature=0)
                system_prompt = (
                    "You are an assistant helping IQAC (Internal Quality Assurance Cell) staff "
                    "at Ganpat University answer questions about their institutional documents "
                    "(NAAC SSR, Annual Reports, NIRF submissions, policies).\n\n"
                    "Answer ONLY using the context sources below. If the answer isn't in the "
                    "context, say so clearly instead of guessing. When you use a fact, cite it "
                    "inline like [Source 1], [Source 2], matching the source numbers given.\n\n"
                    f"CONTEXT:\n{context}"
                )
                response = await llm.ainvoke(
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question},
                    ]
                )
                answer = response.content if hasattr(response, "content") else str(response)

        except LLMProviderError as exc:
            status = RAGChatStatus.ERROR
            error_message = str(exc)
        except Exception as exc:  # noqa: BLE001
            logger.error("rag_chat_failed", error=str(exc))
            status = RAGChatStatus.ERROR
            error_message = f"Something went wrong answering this question: {exc}"

        execution_ms = round((time.perf_counter() - start) * 1000, 1)

        log = RAGChatLog(
            user_id=user_id,
            question=question,
            answer=answer,
            sources=sources,
            status=status,
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
            "answer": answer,
            "sources": sources,
            "status": status.value,
            "execution_ms": execution_ms,
            "error_message": error_message,
            "ai_provider": settings.AI_PROVIDER,
        }


async def get_document_or_404(db: AsyncSession, document_id: uuid.UUID) -> RAGDocument | None:
    result = await db.execute(select(RAGDocument).where(RAGDocument.id == document_id))
    return result.scalar_one_or_none()
