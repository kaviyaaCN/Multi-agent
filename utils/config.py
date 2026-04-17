"""
utils/config.py
===============
Central configuration loader for the Multi-Agent AI Academic Project Assistant.
Reads environment variables from .env and exposes typed settings.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load .env from project root
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env", override=False)


def _load_groq_keys() -> list[str]:
    """
    Load all non-empty GROQ_API_KEY_1 … GROQ_API_KEY_5 from environment.
    Falls back to legacy GROQ_API_KEY if no numbered keys are found.

    Returns:
        List of valid (non-empty) API key strings.
    """
    keys: list[str] = []
    for i in range(1, 6):
        key = os.getenv(f"GROQ_API_KEY_{i}", "").strip()
        if key:
            keys.append(key)

    # Backwards-compatibility: single GROQ_API_KEY
    if not keys:
        legacy = os.getenv("GROQ_API_KEY", "").strip()
        if legacy:
            keys.append(legacy)

    return keys


@dataclass
class Settings:
    """Typed settings container sourced from environment variables."""

    # --- Groq API key pool ---
    groq_api_keys: list[str] = field(default_factory=_load_groq_keys)

    # --- Model ---
    groq_model: str = field(
        default_factory=lambda: os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    )

    # --- Embedding Model ---
    embedding_model: str = field(
        default_factory=lambda: os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    )

    # --- Vector Store ---
    faiss_index_path: Path = field(
        default_factory=lambda: _ROOT / os.getenv("FAISS_INDEX_PATH", "data/faiss_index")
    )

    # --- External APIs ---
    tavily_api_key: str = field(
        default_factory=lambda: os.getenv("TAVILY_API_KEY", "")
    )

    # --- Cache ---
    cache_ttl: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL", "3600"))
    )

    # --- Logging ---
    log_level: str = field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper()
    )

    # --- Paths ---
    data_dir: Path = field(default_factory=lambda: _ROOT / "data")
    docs_dir: Path = field(default_factory=lambda: _ROOT / "data" / "documents")

    # Always Groq
    llm_provider: str = "groq"

    def validate(self) -> None:
        """Raise ValueError if no Groq API keys are configured."""
        if not self.groq_api_keys:
            raise ValueError(
                "No Groq API keys found.\n"
                "Set GROQ_API_KEY_1 (and optionally _2, _3…) in your .env file.\n"
                "Get free keys at: https://console.groq.com/keys"
            )

    @property
    def active_model(self) -> str:
        return self.groq_model

    @property
    def primary_key(self) -> str:
        """Return the first available API key."""
        return self.groq_api_keys[0] if self.groq_api_keys else ""


# Singleton instance used throughout the project
settings = Settings()
