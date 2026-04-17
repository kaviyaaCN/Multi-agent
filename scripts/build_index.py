"""
scripts/build_index.py
======================
Standalone script to rebuild the FAISS vector index from scratch.
Run this whenever you add new documents to data/documents/.

Usage:
    python scripts/build_index.py
    python scripts/build_index.py --docs-dir path/to/your/docs
"""

import sys
import argparse
from pathlib import Path

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rag.embedder import EmbeddingEngine
from rag.document_loader import ingest_directory
from utils.config import settings
from utils.logger import logger


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FAISS index from documents")
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=settings.docs_dir,
        help="Directory containing PDF/TXT/DOCX documents",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=settings.faiss_index_path,
        help="Where to save the FAISS index",
    )
    args = parser.parse_args()

    logger.info("=== FAISS Index Builder ===")
    logger.info("Documents directory: %s", args.docs_dir)
    logger.info("Index output path:   %s", args.index_path)

    if not args.docs_dir.exists():
        logger.error("Documents directory not found: %s", args.docs_dir)
        sys.exit(1)

    engine = EmbeddingEngine()
    count = ingest_directory(args.docs_dir, engine)

    if count == 0:
        logger.warning("No documents were indexed. Check your documents directory.")
        sys.exit(1)

    engine.save(args.index_path)
    logger.info("✅ Index built successfully: %d chunks | %d vectors", count, engine.index.ntotal)
    logger.info("Index saved to: %s", args.index_path)


if __name__ == "__main__":
    main()
