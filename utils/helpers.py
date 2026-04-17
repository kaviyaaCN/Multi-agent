"""
utils/helpers.py
================
Shared utility functions used across agents and UI.
"""

import re
import json
import hashlib
from typing import Any


def clean_llm_output(text: str) -> str:
    """
    Strip markdown code fences and leading/trailing whitespace from LLM output.

    Args:
        text: Raw LLM response string.

    Returns:
        Cleaned plain text.
    """
    # Remove ```python ... ``` or ``` ... ``` blocks
    text = re.sub(r"```[a-zA-Z]*\n?", "", text)
    text = text.replace("```", "")
    return text.strip()


def extract_json_from_text(text: str) -> Any:
    """
    Extract and parse the first valid JSON object or array from a string.

    Args:
        text: Text potentially containing JSON.

    Returns:
        Parsed Python object, or None if not found.
    """
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Locate JSON block within text
    for pattern in (r"\{.*\}", r"\[.*\]"):
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                continue
    return None


def truncate_text(text: str, max_chars: int = 2000) -> str:
    """Truncate text to max_chars, appending '…' if clipped."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"


def compute_hash(text: str) -> str:
    """Return a SHA-256 hex digest of the given text (for deduplication)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def format_similarity_score(score: float) -> str:
    """
    Convert a cosine-similarity score (0–1) to a human-readable label.

    Args:
        score: Float between 0 and 1.

    Returns:
        String like "12.34% similarity — Likely original"
    """
    pct = score * 100
    if pct < 20:
        label = "Likely Original ✅"
    elif pct < 40:
        label = "Low Similarity 🟡"
    elif pct < 60:
        label = "Moderate Similarity 🟠"
    else:
        label = "High Similarity — Review Needed 🔴"
    return f"{pct:.2f}% similarity — {label}"


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks for embedding.

    Args:
        text: Input document text.
        chunk_size: Target characters per chunk.
        overlap: Overlap in characters between consecutive chunks.

    Returns:
        List of text chunks.
    """
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks
