"""
agents/orchestrator.py
======================
Agent Orchestrator
==================
Central controller that manages the multi-agent workflow.
Maintains shared context (memory) across agents, handles sequencing,
and provides a unified interface for the Streamlit frontend.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any

from utils.logger import logger
from utils.config import settings


@dataclass
class SessionMemory:
    """
    Shared context passed between agents during a session.
    Simulates short-term 'memory' for the multi-agent pipeline.
    """
    domain: str = ""
    interest: str = ""
    difficulty: str = "Intermediate"
    selected_topic: Optional[Any] = None        # ProjectTopic dataclass
    documentation: Optional[Any] = None         # ProjectDocumentation
    generated_code: Optional[Any] = None        # GeneratedCode
    plagiarism_report: Optional[Any] = None     # PlagiarismReport
    presentation: Optional[Any] = None          # Presentation
    topics: list = field(default_factory=list)  # List of ProjectTopic
    history: list[str] = field(default_factory=list)  # Action log

    def log_action(self, action: str) -> None:
        """Record an action in the session history."""
        self.history.append(action)
        logger.info(f"[Memory] {action}")

    def reset(self) -> None:
        """Clear session state."""
        self.__init__()
        logger.info("SessionMemory reset.")


class AgentOrchestrator:
    """
    Orchestrates the full multi-agent academic project pipeline.

    Agents are lazy-loaded on first use to save memory.
    Shared memory flows through all stages.

    Usage:
        orch = AgentOrchestrator()
        orch.set_user_context(domain="AI", interest="NLP", difficulty="Advanced")
        topics = orch.run_topic_agent()
        orch.select_topic(topics[0])
        doc = orch.run_documentation_agent()
        code = orch.run_code_agent()
        report = orch.run_plagiarism_agent()
        ppt = orch.run_ppt_agent()
    """

    def __init__(self) -> None:
        self.memory = SessionMemory()
        self._engine = None          # Lazy-loaded EmbeddingEngine
        self._topic_agent = None
        self._doc_agent = None
        self._code_agent = None
        self._plag_agent = None
        self._ppt_agent = None
        logger.info("AgentOrchestrator initialised")

    # ── Setup ──────────────────────────────────────────────────────────────────

    def set_user_context(
        self,
        domain: str,
        interest: str,
        difficulty: str = "Intermediate",
    ) -> None:
        """Store user input in shared memory."""
        self.memory.domain = domain
        self.memory.interest = interest
        self.memory.difficulty = difficulty
        self.memory.log_action(f"User context set: domain={domain}, interest={interest}, difficulty={difficulty}")

    def initialise_rag(self, force_rebuild: bool = False) -> bool:
        """
        Load or build the FAISS index from the documents directory.

        Args:
            force_rebuild: If True, re-index even if a saved index exists.

        Returns:
            True if the engine has indexed documents.
        """
        from rag.embedder import EmbeddingEngine
        from rag.document_loader import ingest_directory

        self._engine = EmbeddingEngine()

        if not force_rebuild and self._engine.load():
            self.memory.log_action(f"RAG index loaded ({self._engine.index.ntotal} vectors)")
            return True

        docs_dir = settings.docs_dir
        if docs_dir.exists():
            count = ingest_directory(docs_dir, self._engine)
            if count > 0:
                self._engine.save()
                self.memory.log_action(f"RAG index built ({count} chunks from {docs_dir})")
                return True

        self.memory.log_action("RAG index empty — agents will use LLM knowledge directly")
        return False

    # ── Lazy agent loaders ────────────────────────────────────────────────────

    def _get_topic_agent(self):
        if self._topic_agent is None:
            from agents.topic_agent import TopicSuggestionAgent
            self._topic_agent = TopicSuggestionAgent(embedding_engine=self._engine)
        return self._topic_agent

    def _get_doc_agent(self):
        if self._doc_agent is None:
            from agents.documentation_agent import DocumentationAgent
            self._doc_agent = DocumentationAgent(embedding_engine=self._engine)
        return self._doc_agent

    def _get_code_agent(self):
        if self._code_agent is None:
            from agents.code_agent import CodeGeneratorAgent
            self._code_agent = CodeGeneratorAgent(embedding_engine=self._engine)
        return self._code_agent

    def _get_plag_agent(self):
        if self._plag_agent is None:
            from agents.plagiarism_agent import PlagiarismCheckerAgent
            from utils.llm_client import get_llm_client
            self._plag_agent = PlagiarismCheckerAgent(
                embedding_engine=self._engine,
                llm_client=get_llm_client(),
            )
        return self._plag_agent

    def _get_ppt_agent(self):
        if self._ppt_agent is None:
            from agents.ppt_agent import PPTGeneratorAgent
            self._ppt_agent = PPTGeneratorAgent()
        return self._ppt_agent

    # ── Agent runners ─────────────────────────────────────────────────────────

    def run_topic_agent(self, count: int = 7) -> list:
        """Run the Topic Suggestion Agent and store results in memory."""
        agent = self._get_topic_agent()
        topics = agent.suggest(
            domain=self.memory.domain,
            interest=self.memory.interest,
            difficulty=self.memory.difficulty,
            count=count,
        )
        self.memory.topics = topics
        self.memory.log_action(f"Topic agent: generated {len(topics)} topics")
        return topics

    def select_topic(self, topic) -> None:
        """Store the user's selected topic in memory."""
        self.memory.selected_topic = topic
        self.memory.log_action(f"Topic selected: {topic.title}")
        
        # Automatically gather dynamic documents and rebuild index
        self.populate_dynamic_documents()

    def populate_dynamic_documents(self) -> int:
        """Fetch web context dynamically using the current topic and domain."""
        from rag.web_scraper import fetch_domain_documents
        
        query_parts = []
        if self.memory.domain:
            query_parts.append(self.memory.domain)
        if self.memory.interest:
            query_parts.append(self.memory.interest)
        if self.memory.selected_topic:
            query_parts.append(f'"{self.memory.selected_topic.title}"')
            query_parts.append("academic research")
        else:
            query_parts.append("academic research project ideas")
            
        query = " ".join(query_parts)
        count = fetch_domain_documents(query)
        if count > 0:
            self.memory.log_action(f"Tavily downloaded {count} web documents.")
            self.initialise_rag(force_rebuild=True)
            
        return count

    def run_documentation_agent(self):
        """Run the Documentation Agent, using the selected topic from memory."""
        if not self.memory.selected_topic:
            raise RuntimeError("No topic selected. Call select_topic() first.")

        topic = self.memory.selected_topic
        agent = self._get_doc_agent()
        doc = agent.generate(
            topic=topic.title,
            domain=self.memory.domain,
            difficulty=self.memory.difficulty,
            technologies=topic.technologies,
        )
        self.memory.documentation = doc
        self.memory.log_action("Documentation agent: report generated")
        return doc

    def run_code_agent(self):
        """Run the Code Generator Agent."""
        if not self.memory.selected_topic:
            raise RuntimeError("No topic selected. Call select_topic() first.")

        topic = self.memory.selected_topic
        agent = self._get_code_agent()
        code = agent.generate(
            topic=topic.title,
            domain=self.memory.domain,
            difficulty=self.memory.difficulty,
            technologies=topic.technologies,
        )
        self.memory.generated_code = code
        self.memory.log_action("Code agent: implementation generated")
        return code

    def run_plagiarism_agent(self, text: Optional[str] = None):
        """Run the Plagiarism Checker Agent against the documentation."""
        if text is None:
            if not self.memory.documentation:
                raise RuntimeError("No documentation available. Run documentation agent first.")
            text = self.memory.documentation.abstract + "\n" + self.memory.documentation.introduction

        agent = self._get_plag_agent()
        report = agent.check(text=text, source_label="Generated Documentation")
        self.memory.plagiarism_report = report
        self.memory.log_action(
            f"Plagiarism agent: score={report.overall_score:.2%}, flagged={report.is_flagged}"
        )
        return report

    def run_ppt_agent(self):
        """Run the PPT Generator Agent using existing documentation from memory."""
        if not self.memory.selected_topic:
            raise RuntimeError("No topic selected. Call select_topic() first.")

        agent = self._get_ppt_agent()
        ppt = agent.generate(
            topic=self.memory.selected_topic.title,
            domain=self.memory.domain,
            documentation=self.memory.documentation,
        )
        self.memory.presentation = ppt
        self.memory.log_action(f"PPT agent: {len(ppt.slides)} slides generated")
        return ppt

    def export_pptx(self, output_path: Optional[Path] = None) -> Path:
        """Export the current presentation to a .pptx file."""
        if not self.memory.presentation:
            raise RuntimeError("No presentation available. Run PPT agent first.")
        agent = self._get_ppt_agent()
        return agent.export_pptx(self.memory.presentation, output_path=output_path)

    def get_status(self) -> dict:
        """Return a dict summarising which pipeline stages are complete."""
        return {
            "context_set": bool(self.memory.domain),
            "topics_generated": len(self.memory.topics) > 0,
            "topic_selected": self.memory.selected_topic is not None,
            "documentation_ready": self.memory.documentation is not None,
            "code_ready": self.memory.generated_code is not None,
            "plagiarism_checked": self.memory.plagiarism_report is not None,
            "presentation_ready": self.memory.presentation is not None,
        }
