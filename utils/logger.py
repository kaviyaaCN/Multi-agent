"""
utils/logger.py
===============
Centralized logging configuration using Loguru.
Every module imports `logger` from here for consistent structured logs.
"""

import sys
from pathlib import Path
from loguru import logger
from utils.config import settings

# ── Remove default loguru handler ──────────────────────────────────────────────
logger.remove()

# ── Console handler ────────────────────────────────────────────────────────────
logger.add(
    sys.stderr,
    level=settings.log_level,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    colorize=True,
)

# ── File handler ───────────────────────────────────────────────────────────────
_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

logger.add(
    _LOG_DIR / "app_{time:YYYY-MM-DD}.log",
    level=settings.log_level,
    rotation="00:00",        # New file every midnight
    retention="7 days",      # Keep one week of logs
    compression="zip",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    enqueue=True,            # Thread-safe async writing
)

__all__ = ["logger"]
