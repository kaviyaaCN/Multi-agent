"""
agents/topic_agent.py
=====================
Topic Suggestion Agent
======================
Retrieves relevant academic context from the RAG corpus and uses the LLM
to generate 5–10 unique, well-described project topics tailored to the
user's domain, interest, and difficulty level.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Optional

from utils.llm_client import get_llm_client
from utils.helpers import extract_json_from_text
from utils.logger import logger


@dataclass
class ProjectTopic:
    """Represents a single suggested project topic."""
    id: int
    title: str
    description: str
    technologies: list[str]
    difficulty: str
    expected_outcome: str


_SYSTEM_PROMPT = """You are an expert academic project advisor specialising in Computer Science, 
AI/ML, and Data Science. Your role is to suggest innovative, feasible, and academically rigorous 
project topics. Always respond ONLY with valid JSON — no prose outside the JSON structure."""

_USER_TEMPLATE = """
A student is looking for academic project ideas with the following profile:
- Domain: {domain}
- Interests: {interest}
- Difficulty Level: {difficulty}

Relevant academic context from research papers:
{context}

Generate exactly {count} unique project topics. Respond with ONLY a valid JSON array like:
[
  {{
    "id": 1,
    "title": "Topic title",
    "description": "2-3 sentence description of the project",
    "technologies": ["Tech1", "Tech2", "Tech3"],
    "difficulty": "{difficulty}",
    "expected_outcome": "What the student will build/demonstrate"
  }},
  ...
]
"""


class TopicSuggestionAgent:
    """
    Agent responsible for generating project topic suggestions.

    Uses RAG to pull relevant academic context before prompting the LLM,
    ensuring suggestions are grounded in real research trends.
    """

    def __init__(self, embedding_engine=None) -> None:
        """
        Args:
            embedding_engine: Optional EmbeddingEngine for RAG context retrieval.
                              If None, the agent works without RAG context.
        """
        self._llm = get_llm_client()
        self._engine = embedding_engine
        logger.info(f"TopicSuggestionAgent initialised (RAG={embedding_engine is not None})")

    def suggest(
        self,
        domain: str,
        interest: str,
        difficulty: str = "Intermediate",
        count: int = 7,
    ) -> list[ProjectTopic]:
        """
        Generate project topic suggestions.

        Args:
            domain: Broad area, e.g. "Machine Learning", "Web Development".
            interest: Specific interest, e.g. "NLP", "Healthcare AI".
            difficulty: "Beginner" | "Intermediate" | "Advanced".
            count: Number of topics to generate (5–10 recommended).

        Returns:
            List of ProjectTopic dataclass instances.
        """
        logger.info(f"TopicAgent.suggest: domain={domain} interest={interest} difficulty={difficulty} count={count}")

        # --- RAG context retrieval ---
        query = f"{domain} {interest} academic projects research"
        context = "No additional context available." 
        if self._engine:
            try:
                context = self._engine.get_context(query, top_k=5, max_chars=2000)
            except Exception as exc:
                logger.warning(f"RAG retrieval failed: {exc}")

        # --- Build and send prompt ---
        prompt = _USER_TEMPLATE.format(
            domain=domain,
            interest=interest,
            difficulty=difficulty,
            context=context,
            count=count,
        )

        raw = self._llm.generate(
            prompt=prompt,
            system_instruction=_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=1500,
        )
        logger.debug(f"TopicAgent raw response (first 200): {raw[:200]}")

        # --- Parse JSON ---
        topics_data = extract_json_from_text(raw)
        if not isinstance(topics_data, list):
            logger.error("TopicAgent: unexpected response format — using fallback")
            topics_data = self._fallback_topics(domain, interest, difficulty, count)

        topics = []
        for item in topics_data[:count]:
            try:
                topics.append(ProjectTopic(
                    id=item.get("id", len(topics) + 1),
                    title=item.get("title", "Untitled Topic"),
                    description=item.get("description", ""),
                    technologies=item.get("technologies", []),
                    difficulty=item.get("difficulty", difficulty),
                    expected_outcome=item.get("expected_outcome", ""),
                ))
            except Exception as exc:
                logger.warning(f"Skipping malformed topic item: {exc}")

        logger.info(f"TopicAgent returning {len(topics)} topics")
        return topics

    # ── Fallback ───────────────────────────────────────────────────────────────

    def _fallback_topics(
        self, domain: str, interest: str, difficulty: str, count: int
    ) -> list[dict]:
        """
        Return generic fallback topics when LLM JSON parsing fails.
        This ensures the app never crashes due to an LLM format error.
        """
        logger.warning("Using hardcoded fallback topics")
        return [
            {
                "id": i + 1,
                "title": f"{domain} Project {i + 1}: {interest} Application",
                "description": f"A {difficulty.lower()}-level project applying {interest} concepts in {domain}.",
                "technologies": ["Python", "TensorFlow", "Streamlit"],
                "difficulty": difficulty,
                "expected_outcome": f"A working prototype demonstrating {interest} techniques.",
            }
            for i in range(count)
        ]
