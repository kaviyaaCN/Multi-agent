"""
utils/llm_client.py
===================
Groq LLM client with smart API key rotation.

When a key hits a rate limit (HTTP 429), the client:
1. Reads the exact retry_delay from the error response
2. Tries the next key immediately (without waiting)
3. After all keys are tried, waits for the longest retry_delay + buffer
4. Repeats until a key succeeds or permanent failure is detected
"""

import re
import time
import threading
from functools import lru_cache
from typing import Optional

from cachetools import TTLCache

from utils.config import settings
from utils.logger import logger

# ── In-memory response cache ───────────────────────────────────────────────────
_cache: TTLCache = TTLCache(maxsize=256, ttl=settings.cache_ttl)

# Keywords that identify rate-limit / quota errors
_RATE_LIMIT_SIGNALS = (
    "429",
    "quota",
    "rate",
    "rate_limit_exceeded",
    "too many requests",
)


def _is_rate_limit_error(exc: Exception) -> bool:
    """Return True if the exception is a rate-limit / quota error."""
    msg = str(exc).lower()
    return any(signal in msg for signal in _RATE_LIMIT_SIGNALS)


def _extract_retry_delay(exc: Exception) -> float:
    """
    Parse the recommended retry delay (in seconds) from a 429 error message.
    Groq formats delays like "Please try again in 14.384s" or "8m50.41s".
    """
    msg = str(exc)

    # Pattern: "try again in 17.729s"
    match = re.search(r"try again in (\d+(?:\.\d+)?)s", msg, re.IGNORECASE)
    if match:
        return float(match.group(1))
        
    # Pattern: "try again in 8m50.41s"
    match = re.search(r"try again in (\d+)m(\d+(?:\.\d+)?)s", msg, re.IGNORECASE)
    if match:
        return float(match.group(1)) * 60 + float(match.group(2))

    # Safe default if we can't parse the delay
    return 30.0


class LLMClient:
    """
    Groq LLM client with intelligent API key rotation.
    """

    _RETRY_BUFFER = 10       # Extra seconds added on top of API's retry_delay
    _MAX_FULL_CYCLES = 3     # Stop after this many full cycles with no success

    def __init__(self) -> None:
        from groq import Groq
        self._GroqClass = Groq
        self._model_name = settings.groq_model
        self._keys = settings.groq_api_keys
        self._lock = threading.Lock()
        self._current_idx = 0

        if not self._keys:
            raise RuntimeError(
                "No Groq API keys configured. "
                "Set GROQ_API_KEY_1 in your .env file."
            )

        self._clients = self._build_clients()

        logger.info(
            f"LLMClient initialised: model={self._model_name}, "
            f"keys={len(self._keys)} configured"
        )

    # ── Setup ──────────────────────────────────────────────────────────────────

    def _build_clients(self) -> list:
        """Create one Client per API key."""
        clients = []
        for i, key in enumerate(self._keys, 1):
            client = self._GroqClass(api_key=key)
            clients.append(client)
            logger.debug(f"Registered Groq key #{i} (****{key[-4:]})")
        return clients

    # ── Key rotation helpers ───────────────────────────────────────────────────

    def _rotate(self) -> int:
        """Advance to the next key (thread-safe). Returns the new index."""
        with self._lock:
            self._current_idx = (self._current_idx + 1) % len(self._clients)
            return self._current_idx

    def _key_label(self, idx: int) -> str:
        return f"key#{idx + 1} (****{self._keys[idx][-4:]})"

    # ── Core generate ──────────────────────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        use_cache: bool = True,
    ) -> str:
        """
        Generate text from Groq with smart key rotation on 429.
        """
        cache_key = hash((prompt, system_instruction, temperature, max_tokens))
        if use_cache and cache_key in _cache:
            logger.debug(f"Cache HIT for prompt hash {cache_key}")
            return _cache[cache_key]

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        n_keys = len(self._clients)
        start_idx = self._current_idx  # Remember which key we started on

        for cycle in range(self._MAX_FULL_CYCLES):
            per_key_delays: list[float] = []

            # Try every key once per cycle
            for offset in range(n_keys):
                idx = (start_idx + offset) % n_keys

                try:
                    t0 = time.perf_counter()
                    # Updated to explicitly use max_completion_tokens if supported, else max_tokens fallback for Groq API
                    response = self._clients[idx].chat.completions.create(
                        model=self._model_name,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    elapsed = time.perf_counter() - t0
                    text = response.choices[0].message.content or ""

                    # Stick with this working key for the next call
                    with self._lock:
                        self._current_idx = idx

                    logger.info(
                        f"LLM response in {elapsed:.2f}s ({len(text)} chars) "
                        f"via {self._key_label(idx)}"
                    )
                    if use_cache:
                        _cache[cache_key] = text
                    return text

                except Exception as exc:
                    if not _is_rate_limit_error(exc):
                        # e.g., 403 Project Denied, 400 Bad Request
                        # Treat as permanently broken for this cycle, but DO NOT crash yet.
                        # Move to the next key in the pool.
                        logger.error(
                            f"{self._key_label(idx)} failed (non-rate-limit): {exc} — trying next key"
                        )
                        continue

                    delay = _extract_retry_delay(exc)
                    per_key_delays.append(delay)
                    logger.warning(
                        f"{self._key_label(idx)} rate-limited "
                        f"(API says retry in {delay:.0f}s) — trying next key"
                    )
                    # Small pause before switching keys
                    time.sleep(2)

            # All keys tried — wait for the API's recommended delay
            if per_key_delays:
                wait = max(per_key_delays) + self._RETRY_BUFFER
                logger.warning(
                    f"All {n_keys} Groq keys rate-limited on cycle {cycle + 1}/"
                    f"{self._MAX_FULL_CYCLES}. "
                    f"Waiting {wait:.0f}s (API max delay={max(per_key_delays):.0f}s "
                    f"+ {self._RETRY_BUFFER}s buffer)…"
                )
                time.sleep(wait)
            else:
                break  # Should not happen if all keys are valid rate limits, but handles 403 fallback

        # All cycles exhausted
        msg = (
            f"All {n_keys} Groq keys are rate-limited after "
            f"{self._MAX_FULL_CYCLES} retry cycles. "
            "Wait a few minutes and try again, or add more API keys."
        )
        logger.error(msg)
        raise RuntimeError(msg)


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    """Return the singleton LLMClient (lazy-initialized)."""
    return LLMClient()
