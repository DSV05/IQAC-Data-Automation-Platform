"""
Module 7 — RAG Chatbot
=======================
Extracts per-page text from a PDF so it can be chunked and embedded.
Kept as a thin wrapper around pypdf so the rest of the ingestion
pipeline doesn't care which PDF library is underneath.
"""
from pathlib import Path


class PDFExtractionError(Exception):
    pass


def extract_pages(file_path: str | Path) -> list[str]:
    """
    Returns a list of strings, one per page, in page order (index 0 = page 1).
    Pages with no extractable text (e.g. pure scanned images) come back as "".
    """
    from pypdf import PdfReader

    try:
        reader = PdfReader(str(file_path))
    except Exception as exc:  # noqa: BLE001
        raise PDFExtractionError(f"Could not open PDF: {exc}") from exc

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:  # noqa: BLE001
            raise PDFExtractionError("PDF is password-protected and could not be opened.") from exc

    pages: list[str] = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:  # noqa: BLE001
            text = ""
        pages.append(text.strip())

    if not any(p for p in pages):
        raise PDFExtractionError(
            "No extractable text found in this PDF. It may be a scanned/image-only "
            "document — OCR is not currently supported."
        )

    return pages
