"""
rag/embedder.py
===============
Embedding engine using sentence-transformers + FAISS.
Handles document ingestion, index persistence, and semantic retrieval.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Optional

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from utils.config import settings
from utils.helpers import chunk_text, compute_hash
from utils.logger import logger


class EmbeddingEngine:
    """
    Manages a FAISS vector index for semantic document search.

    Attributes:
        model: The SentenceTransformer embedding model.
        index: FAISS flat-L2 index.
        texts: Raw text chunks stored in insertion order.
        metadata: Per-chunk metadata (source filename, etc.).
    """

    _DIMENSION_MAP: dict[str, int] = {
        "all-MiniLM-L6-v2": 384,
        "all-mpnet-base-v2": 768,
        "paraphrase-MiniLM-L6-v2": 384,
    }

    def __init__(self, model_name: Optional[str] = None) -> None:
        model_name = model_name or settings.embedding_model
        self.model = SentenceTransformer(model_name)
        self._dim = self._DIMENSION_MAP.get(model_name, 384)
        self.index: faiss.IndexFlatL2 = faiss.IndexFlatL2(self._dim)
        self.texts: list[str] = []
        self.metadata: list[dict] = []
        self._seen_hashes: set[str] = set()
        logger.info("EmbeddingEngine ready: model=%s dim=%d", model_name, self._dim)

    # ── Ingestion ──────────────────────────────────────────────────────────────

    def add_document(
        self,
        text: str,
        source: str = "unknown",
        chunk_size: int = 500,
        overlap: int = 50,
    ) -> int:
        """
        Chunk and embed a raw text document, adding it to the FAISS index.

        Args:
            text: Full document text.
            source: Filename or identifier for provenance.
            chunk_size: Characters per chunk.
            overlap: Overlap between consecutive chunks.

        Returns:
            Number of new chunks added.
        """
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        new_chunks: list[str] = []
        new_meta: list[dict] = []

        for i, chunk in enumerate(chunks):
            h = compute_hash(chunk)
            if h in self._seen_hashes:
                continue  # Skip duplicates
            self._seen_hashes.add(h)
            new_chunks.append(chunk)
            new_meta.append({"source": source, "chunk_id": i, "hash": h})

        if not new_chunks:
            logger.debug("No new unique chunks from source=%s", source)
            return 0

        embeddings = self.model.encode(new_chunks, show_progress_bar=False)
        embeddings = np.array(embeddings, dtype="float32")
        self.index.add(embeddings)
        self.texts.extend(new_chunks)
        self.metadata.extend(new_meta)

        logger.info("Added %d chunks from source=%s (total=%d)", len(new_chunks), source, len(self.texts))
        return len(new_chunks)

    # ── Retrieval ──────────────────────────────────────────────────────────────

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Retrieve the top-k most semantically similar chunks.

        Args:
            query: User query string.
            top_k: Number of results to return.

        Returns:
            List of dicts with keys: text, source, score.
        """
        if self.index.ntotal == 0:
            logger.warning("FAISS index is empty — no documents ingested yet.")
            return []

        q_emb = self.model.encode([query], show_progress_bar=False)
        q_emb = np.array(q_emb, dtype="float32")
        distances, indices = self.index.search(q_emb, min(top_k, self.index.ntotal))

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            # Convert L2 distance to a 0-1 similarity score
            similarity = float(1 / (1 + dist))
            results.append({
                "text": self.texts[idx],
                "source": self.metadata[idx]["source"],
                "score": round(similarity, 4),
            })
        return results

    def get_context(self, query: str, top_k: int = 5, max_chars: int = 3000) -> str:
        """
        Return a formatted context string from top retrieved chunks.

        Args:
            query: The search query.
            top_k: Chunks to retrieve.
            max_chars: Maximum total characters to return.

        Returns:
            Concatenated relevant context.
        """
        results = self.search(query, top_k=top_k)
        if not results:
            return "No relevant context found in the knowledge base."

        context_parts = []
        total = 0
        for r in results:
            snippet = f"[Source: {r['source']}]\n{r['text']}"
            if total + len(snippet) > max_chars:
                break
            context_parts.append(snippet)
            total += len(snippet)

        return "\n\n---\n\n".join(context_parts)

    # ── Similarity scoring (for plagiarism) ───────────────────────────────────

    def compute_similarity(self, text_a: str, text_b: str) -> float:
        """
        Compute cosine similarity between two texts.

        Args:
            text_a: First text.
            text_b: Second text.

        Returns:
            Cosine similarity float in [0, 1].
        """
        vecs = self.model.encode([text_a, text_b], show_progress_bar=False)
        a, b = vecs[0], vecs[1]
        cos_sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
        return max(0.0, min(1.0, cos_sim))

    # ── Persistence ────────────────────────────────────────────────────────────

    def save(self, path: Optional[Path] = None) -> None:
        """Persist the FAISS index and text corpus to disk."""
        path = path or settings.faiss_index_path
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path / "index.faiss"))
        with open(path / "corpus.pkl", "wb") as f:
            pickle.dump({"texts": self.texts, "metadata": self.metadata, "hashes": self._seen_hashes}, f)
        logger.info("Index saved to %s (%d vectors)", path, self.index.ntotal)

    def load(self, path: Optional[Path] = None) -> bool:
        """
        Load a previously saved FAISS index from disk.

        Returns:
            True if successfully loaded, False if files not found.
        """
        path = path or settings.faiss_index_path
        path = Path(path)
        index_file = path / "index.faiss"
        corpus_file = path / "corpus.pkl"

        if not index_file.exists() or not corpus_file.exists():
            logger.info("No saved index found at %s — starting fresh.", path)
            return False

        self.index = faiss.read_index(str(index_file))
        with open(corpus_file, "rb") as f:
            data = pickle.load(f)
        self.texts = data["texts"]
        self.metadata = data["metadata"]
        self._seen_hashes = data.get("hashes", set())
        logger.info("Loaded index from %s (%d vectors)", path, self.index.ntotal)
        return True
