"""
utils/metrics.py
================
Evaluation metrics for assessing agent output quality.
Used for academic grading and system self-evaluation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class DocumentationMetrics:
    """Quality metrics for generated documentation."""
    word_count: int
    section_count: int
    has_references: bool
    avg_section_length: float
    readability_score: float  # Flesch reading ease approximation
    quality_label: str

    def to_dict(self) -> dict:
        return {
            "word_count": self.word_count,
            "section_count": self.section_count,
            "has_references": self.has_references,
            "avg_section_length": round(self.avg_section_length, 1),
            "readability_score": round(self.readability_score, 1),
            "quality_label": self.quality_label,
        }


@dataclass
class CodeMetrics:
    """Quality metrics for generated code."""
    line_count: int
    function_count: int
    class_count: int
    comment_ratio: float      # Comments / total lines
    has_docstrings: bool
    has_error_handling: bool
    quality_label: str

    def to_dict(self) -> dict:
        return {
            "line_count": self.line_count,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "comment_ratio": round(self.comment_ratio, 2),
            "has_docstrings": self.has_docstrings,
            "has_error_handling": self.has_error_handling,
            "quality_label": self.quality_label,
        }


def evaluate_documentation(doc) -> DocumentationMetrics:
    """
    Compute quality metrics for a ProjectDocumentation object.

    Args:
        doc: ProjectDocumentation instance.

    Returns:
        DocumentationMetrics dataclass.
    """
    sections = [
        doc.abstract, doc.introduction, doc.literature_survey,
        doc.methodology, doc.results_and_discussion,
        doc.conclusion, doc.future_work,
    ]
    non_empty = [s for s in sections if s and len(s.strip()) > 50]
    all_text = " ".join(non_empty)
    words = all_text.split()
    word_count = len(words)

    # Avg section length
    avg_len = word_count / len(non_empty) if non_empty else 0

    # Approximate Flesch Reading Ease
    sentences = re.split(r"[.!?]+", all_text)
    sentences = [s.strip() for s in sentences if s.strip()]
    n_sentences = max(len(sentences), 1)
    syllables = sum(_count_syllables(w) for w in words)
    flesch = 206.835 - 1.015 * (word_count / n_sentences) - 84.6 * (syllables / max(word_count, 1))
    flesch = max(0.0, min(100.0, flesch))

    # Quality label
    if word_count > 2000 and len(non_empty) >= 6:
        label = "Excellent 🌟"
    elif word_count > 1000 and len(non_empty) >= 4:
        label = "Good ✅"
    elif word_count > 500:
        label = "Fair 🟡"
    else:
        label = "Needs Improvement 🔴"

    return DocumentationMetrics(
        word_count=word_count,
        section_count=len(non_empty),
        has_references=len(doc.references) > 0,
        avg_section_length=avg_len,
        readability_score=flesch,
        quality_label=label,
    )


def evaluate_code(code_text: str) -> CodeMetrics:
    """
    Compute quality metrics for a Python code string.

    Args:
        code_text: Raw Python source code.

    Returns:
        CodeMetrics dataclass.
    """
    lines = code_text.splitlines()
    total = len(lines)
    comment_lines = sum(1 for l in lines if l.strip().startswith("#"))
    comment_ratio = comment_lines / max(total, 1)

    func_count = len(re.findall(r"^\s*def\s+\w+", code_text, re.MULTILINE))
    class_count = len(re.findall(r"^\s*class\s+\w+", code_text, re.MULTILINE))
    has_docstrings = '"""' in code_text or "'''" in code_text
    has_error_handling = "try:" in code_text or "except" in code_text

    # Quality label
    score = 0
    if total > 50:     score += 1
    if func_count > 2: score += 1
    if class_count > 0: score += 1
    if has_docstrings: score += 1
    if comment_ratio > 0.1: score += 1
    if has_error_handling: score += 1

    labels = {6: "Excellent 🌟", 5: "Excellent 🌟", 4: "Good ✅",
              3: "Fair 🟡", 2: "Fair 🟡", 1: "Needs Improvement 🔴", 0: "Needs Improvement 🔴"}
    label = labels.get(score, "Fair 🟡")

    return CodeMetrics(
        line_count=total,
        function_count=func_count,
        class_count=class_count,
        comment_ratio=comment_ratio,
        has_docstrings=has_docstrings,
        has_error_handling=has_error_handling,
        quality_label=label,
    )


def _count_syllables(word: str) -> int:
    """Approximate syllable count for Flesch score calculation."""
    word = word.lower().strip(".,;:!?\"'")
    if not word:
        return 0
    count = len(re.findall(r"[aeiou]+", word))
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)
