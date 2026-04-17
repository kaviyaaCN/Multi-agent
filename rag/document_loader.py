"""
rag/document_loader.py
======================
Ingests PDF, TXT, and DOCX files from the data/documents directory
and feeds them into the EmbeddingEngine.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from utils.logger import logger

# Graceful optional imports
try:
    import fitz  # PyMuPDF
    _PYMUPDF_OK = True
except ImportError:
    _PYMUPDF_OK = False
    logger.warning("PyMuPDF not installed — PDF loading unavailable.")

try:
    from docx import Document as DocxDocument
    _DOCX_OK = True
except ImportError:
    _DOCX_OK = False
    logger.warning("python-docx not installed — DOCX loading unavailable.")


def load_pdf(file_path: Path) -> str:
    """Extract all text from a PDF using PyMuPDF."""
    if not _PYMUPDF_OK:
        raise ImportError("Install PyMuPDF: pip install PyMuPDF")
    doc = fitz.open(str(file_path))
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    logger.debug("Extracted %d chars from PDF: %s", len(text), file_path.name)
    return text


def load_txt(file_path: Path) -> str:
    """Read plain text file with UTF-8 encoding."""
    text = file_path.read_text(encoding="utf-8", errors="replace")
    logger.debug("Loaded %d chars from TXT: %s", len(text), file_path.name)
    return text


def load_docx(file_path: Path) -> str:
    """Extract text from a DOCX Word document."""
    if not _DOCX_OK:
        raise ImportError("Install python-docx: pip install python-docx")
    doc = DocxDocument(str(file_path))
    text = "\n".join(para.text for para in doc.paragraphs)
    logger.debug("Extracted %d chars from DOCX: %s", len(text), file_path.name)
    return text


def load_file(file_path: Path) -> Optional[str]:
    """
    Dispatch to the correct loader based on file extension.

    Returns:
        Extracted text, or None if the format is unsupported.
    """
    suffix = file_path.suffix.lower()
    try:
        if suffix == ".pdf":
            return load_pdf(file_path)
        elif suffix == ".txt":
            return load_txt(file_path)
        elif suffix in (".docx", ".doc"):
            return load_docx(file_path)
        else:
            logger.warning("Unsupported file type: %s", suffix)
            return None
    except Exception as exc:
        logger.error("Failed to load %s: %s", file_path.name, exc)
        return None


def ingest_directory(directory: Path, engine) -> int:
    """
    Walk a directory, extract text from every supported file,
    and add it to the EmbeddingEngine.

    Args:
        directory: Root path to scan.
        engine: An EmbeddingEngine instance.

    Returns:
        Total number of chunks indexed.
    """
    supported = {".pdf", ".txt", ".docx", ".doc"}
    total_chunks = 0
    files = [f for f in directory.rglob("*") if f.suffix.lower() in supported]

    if not files:
        logger.warning("No supported documents found in %s", directory)
        return 0

    logger.info("Ingesting %d file(s) from %s", len(files), directory)
    for file_path in files:
        text = load_file(file_path)
        if text and text.strip():
            total_chunks += engine.add_document(text, source=file_path.name)

    logger.info("Ingestion complete — %d total chunks indexed.", total_chunks)
    return total_chunks
