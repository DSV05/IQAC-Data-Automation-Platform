"""
Module 7 — RAG Chatbot
=======================
Thin manager around a single on-disk FAISS index shared by every
ingested document. An asyncio lock serializes writes so two uploads
processed at the same time can't corrupt the index file — this is a
single-process safeguard (fine for the one Uvicorn worker this app
runs today; a multi-worker deployment would need a real lock, e.g. Redis).
"""
import asyncio
import os
from pathlib import Path

from app.core.config import get_settings
from app.utils.llm_provider import get_embeddings

settings = get_settings()
_write_lock = asyncio.Lock()


def _index_exists() -> bool:
    index_path = Path(settings.RAG_INDEX_DIR) / "index.faiss"
    return index_path.exists()


def _load_or_create(embeddings):
    from langchain_community.vectorstores import FAISS
    from langchain_community.docstore.in_memory import InMemoryDocstore
    import faiss

    if _index_exists():
        return FAISS.load_local(
            settings.RAG_INDEX_DIR, embeddings, allow_dangerous_deserialization=True
        )

    # Bootstrap an empty index sized for the embedding model's output dimension.
    probe_vec = embeddings.embed_query("dimension probe")
    dim = len(probe_vec)
    index = faiss.IndexFlatL2(dim)
    return FAISS(
        embedding_function=embeddings,
        index=index,
        docstore=InMemoryDocstore({}),
        index_to_docstore_id={},
    )


async def add_documents(langchain_docs: list) -> list[str]:
    """Embeds and adds LangChain Document objects to the shared index. Returns their ids."""
    async with _write_lock:
        os.makedirs(settings.RAG_INDEX_DIR, exist_ok=True)
        embeddings = get_embeddings()
        store = await asyncio.to_thread(_load_or_create, embeddings)
        ids = await asyncio.to_thread(store.add_documents, langchain_docs)
        await asyncio.to_thread(store.save_local, settings.RAG_INDEX_DIR)
        return ids


async def delete_ids(ids: list[str]) -> None:
    """Removes vectors by id (e.g. when a document is deleted) and persists the index."""
    if not ids or not _index_exists():
        return
    async with _write_lock:
        embeddings = get_embeddings()
        store = await asyncio.to_thread(_load_or_create, embeddings)
        await asyncio.to_thread(store.delete, ids)
        await asyncio.to_thread(store.save_local, settings.RAG_INDEX_DIR)


async def similarity_search(query: str, k: int, document_id: str | None = None):
    """
    Returns a list of (Document, score) tuples, lowest distance (best match) first.
    If document_id is given, restricts results to chunks from that document.
    """
    if not _index_exists():
        return []
    embeddings = get_embeddings()
    store = await asyncio.to_thread(_load_or_create, embeddings)

    filter_fn = None
    if document_id:
        filter_fn = {"document_id": document_id}

    # Over-fetch a bit when filtering, since FAISS filters after the ANN search.
    fetch_k = k * 4 if filter_fn else k
    results = await asyncio.to_thread(
        store.similarity_search_with_score, query, k=fetch_k, filter=filter_fn
    )
    return results[:k]
