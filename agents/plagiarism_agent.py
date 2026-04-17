"""
agents/plagiarism_agent.py
===========================
Plagiarism Checker Agent
========================
Uses semantic embeddings to compare generated content against indexed
documents in the FAISS corpus, reporting cosine-similarity scores
and identifying the most similar source passages.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from utils.helpers import format_similarity_score, chunk_text, truncate_text
from utils.logger import logger


@dataclass
class PlagiarismReport:
    """Full plagiarism analysis report."""
    overall_score: float                         # 0–1 cosine similarity
    verdict: str                                 # Human-readable label
    top_matches: list[dict] = field(default_factory=list)   # top matching chunks
    chunk_scores: list[float] = field(default_factory=list) # per-chunk scores
    summary: str = ""

    @property
    def is_flagged(self) -> bool:
        """True if overall similarity exceeds the 40% threshold."""
        return self.overall_score > 0.40

    def to_markdown(self) -> str:
        """Return a formatted markdown report."""
        lines = [
            f"## Plagiarism Report\n",
            f"**Overall Similarity:** {format_similarity_score(self.overall_score)}\n",
            f"**Verdict:** {self.verdict}\n\n",
        ]
        if self.top_matches:
            lines.append("### Top Matching Passages\n")
            for i, m in enumerate(self.top_matches[:3], 1):
                lines.append(
                    f"**Match {i}** (Score: {m['score']:.2%}, Source: `{m['source']}`)\n"
                    f"> {truncate_text(m['text'], 200)}\n"
                )
        lines.append(f"\n### Summary\n{self.summary}")
        return "\n".join(lines)


class PlagiarismCheckerAgent:
    """
    Agent that checks the originality of generated text.

    Strategy:
    1. Split the content into chunks.
    2. For each chunk, query FAISS for most similar indexed passage.
    3. Aggregate scores and identify flagged sections.
    4. Generate a natural-language summary via LLM.
    """

    # Similarity thresholds
    _THRESHOLDS = {
        "original":   (0.00, 0.20),
        "low":        (0.20, 0.40),
        "moderate":   (0.40, 0.60),
        "high":       (0.60, 1.00),
    }

    def __init__(self, embedding_engine=None, llm_client=None) -> None:
        """
        Args:
            embedding_engine: EmbeddingEngine instance for similarity computation.
                              If None, a lightweight fallback is used.
            llm_client: Optional LLMClient for generating natural-language summaries.
        """
        self._engine = embedding_engine
        self._llm = llm_client
        logger.info(
            "PlagiarismCheckerAgent initialised (engine=%s, llm=%s)",
            embedding_engine is not None, llm_client is not None,
        )

    def check(
        self,
        text: str,
        source_label: str = "Generated Content",
        chunk_size: int = 400,
    ) -> PlagiarismReport:
        """
        Analyse the input text for similarity against the indexed corpus.

        Args:
            text: The text to check (e.g. generated documentation).
            source_label: Label for logging/display.
            chunk_size: Characters per analysis chunk.

        Returns:
            PlagiarismReport with scores and matched passages.
        """
        logger.info(
            "PlagiarismAgent.check: label=%s len=%d", source_label, len(text)
        )

        if not text.strip():
            return PlagiarismReport(
                overall_score=0.0,
                verdict="No content to analyse",
                summary="Empty input was provided.",
            )

        if self._engine is None or self._engine.index.ntotal == 0:
            return self._fallback_report(text)

        # Split content into chunks for fine-grained analysis
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=50)
        logger.debug("Checking %d chunks", len(chunks))

        chunk_scores: list[float] = []
        top_matches: list[dict] = []

        for chunk in chunks:
            if len(chunk.strip()) < 50:
                continue  # Skip very short chunks

            results = self._engine.search(chunk, top_k=1)
            if results:
                best = results[0]
                score = best["score"]
                chunk_scores.append(score)
                if score > 0.30:  # Only record meaningful matches
                    top_matches.append({
                        "text": chunk,
                        "source": best["source"],
                        "score": score,
                        "matched_text": best["text"],
                    })

        # Aggregate
        if chunk_scores:
            overall = float(sum(chunk_scores) / len(chunk_scores))
        else:
            overall = 0.0

        # Sort top matches by score
        top_matches.sort(key=lambda x: x["score"], reverse=True)

        verdict = self._get_verdict(overall)
        summary = self._generate_summary(overall, top_matches, source_label)

        report = PlagiarismReport(
            overall_score=round(overall, 4),
            verdict=verdict,
            top_matches=top_matches[:5],
            chunk_scores=chunk_scores,
            summary=summary,
        )

        logger.info(
            "PlagiarismAgent complete: score=%.4f verdict=%s flagged=%s",
            overall, verdict, report.is_flagged,
        )
        return report

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _get_verdict(self, score: float) -> str:
        for label, (low, high) in self._THRESHOLDS.items():
            if low <= score < high:
                return {
                    "original": "✅ Likely Original — Safe to submit",
                    "low": "🟡 Low Similarity — Minor review recommended",
                    "moderate": "🟠 Moderate Similarity — Review and paraphrase flagged sections",
                    "high": "🔴 High Similarity — Significant revision required",
                }[label]
        return "Unknown"

    def _generate_summary(
        self,
        score: float,
        matches: list[dict],
        source_label: str,
    ) -> str:
        """Use LLM to write a natural-language summary, or use a template fallback."""
        if self._llm and score > 0.20:
            match_details = "\n".join(
                f"- Score {m['score']:.2%} with source {m['source']!r}"
                for m in matches[:3]
            )
            prompt = f"""Write a 3-4 sentence plagiarism analysis summary for:
Content: "{source_label}"
Overall similarity score: {score:.2%}
Top matches:
{match_details if match_details else "None found"}

Be factual and suggest concrete next steps."""
            try:
                return self._llm.generate(prompt=prompt, temperature=0.3, max_tokens=200)
            except Exception as exc:
                logger.warning("LLM summary generation failed: %s", exc)

        # Template fallback
        pct = score * 100
        if pct < 20:
            return (
                f"The content shows {pct:.1f}% similarity to indexed documents. "
                "It appears substantially original and is suitable for submission."
            )
        elif pct < 40:
            return (
                f"The content shows {pct:.1f}% similarity. Some passages have minor "
                "overlap with existing documents. Consider reviewing the flagged sections."
            )
        else:
            return (
                f"The content shows {pct:.1f}% similarity to indexed documents. "
                "Significant revision is recommended before submission. "
                "Paraphrase or cite the flagged sections appropriately."
            )

    def _fallback_report(self, text: str) -> PlagiarismReport:
        """Return a safe fallback when no index is available."""
        logger.warning("No FAISS index — using heuristic originality estimate")
        word_count = len(text.split())
        estimated_score = min(0.15, word_count / 10000)  # Simple heuristic
        return PlagiarismReport(
            overall_score=estimated_score,
            verdict="✅ Likely Original (index unavailable — heuristic only)",
            summary=(
                "No indexed documents are available for comparison. "
                "Add academic PDFs to data/documents/ and rebuild the index "
                "for accurate plagiarism detection. "
                f"Heuristic score based on text length: {estimated_score:.2%}."
            ),
        )
