"""Centralized logging configuration — inspired by Log4j.

Features:
  - Console handler with color-coded output (like Log4j ConsoleAppender)
  - Rotating file handler for all logs  (like Log4j RollingFileAppender)
  - Separate error-only file handler    (like Log4j ThresholdFilter)
  - Structured format: timestamp | level | logger | thread | message
  - Configurable via environment variables (LOG_LEVEL, LOG_DIR)
  - SQL query logging control (LOG_SQL)
  - Uvicorn/FastAPI access log integration

Usage:
    from app.core.logging_config import setup_logging
    setup_logging()  # Call once at application startup
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────
# Log format patterns (inspired by Log4j PatternLayout)
# ─────────────────────────────────────────────────────────────────────

# Full format: 2026-04-04 10:15:30.123 | INFO     | app.api.v1.auth | MainThread | Login success
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-40s | %(threadName)-12s | %(message)s"

# Compact format for console (colored)
CONSOLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"

# Date format matching ISO-8601
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ─────────────────────────────────────────────────────────────────────
# Color handler for console (like Log4j HighlightConverter)
# ─────────────────────────────────────────────────────────────────────

class ColoredFormatter(logging.Formatter):
    """Adds ANSI color codes to log levels for terminal output."""

    COLORS = {
        logging.DEBUG:    "\033[36m",   # Cyan
        logging.INFO:     "\033[32m",   # Green
        logging.WARNING:  "\033[33m",   # Yellow
        logging.ERROR:    "\033[31m",   # Red
        logging.CRITICAL: "\033[1;31m", # Bold Red
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


# ─────────────────────────────────────────────────────────────────────
# Setup function
# ─────────────────────────────────────────────────────────────────────

def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_sql: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB per file
    backup_count: int = 5,              # Keep 5 rotated files
) -> None:
    """Configure the root logger with console + file handlers.

    Equivalent to a Log4j XML configuration with:
      - ConsoleAppender (STDOUT, colored, all levels)
      - RollingFileAppender ("logs/app.log", all levels, 10MB rotation x5)
      - RollingFileAppender ("logs/error.log", ERROR+ only, 10MB rotation x5)

    Args:
        log_level: Root log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_dir: Directory for log files. Created automatically.
        log_sql: If True, enable SQLAlchemy SQL echo at DEBUG level.
        max_bytes: Max size per log file before rotation.
        backup_count: Number of rotated backup files to keep.
    """
    # Resolve level
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # ── Root logger ──────────────────────────────────────────────────
    root = logging.getLogger()
    root.setLevel(level)

    # Clear any existing handlers to avoid duplicates on reload
    root.handlers.clear()

    # ── Handler 1: Console (like Log4j ConsoleAppender) ──────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(ColoredFormatter(CONSOLE_FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(console_handler)

    # ── Handler 2: All-level file (like Log4j RollingFileAppender) ───
    app_file = log_path / "app.log"
    file_handler = RotatingFileHandler(
        filename=str(app_file),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(file_handler)

    # ── Handler 3: Error-only file (like Log4j ThresholdFilter) ──────
    error_file = log_path / "error.log"
    error_handler = RotatingFileHandler(
        filename=str(error_file),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(error_handler)

    # ── SQLAlchemy engine logging ────────────────────────────────────
    sa_logger = logging.getLogger("sqlalchemy.engine")
    sa_logger.setLevel(logging.DEBUG if log_sql else logging.WARNING)
    sa_logger.propagate = True

    # ── Suppress noisy third-party loggers ───────────────────────────
    for noisy in ("httpcore", "httpx", "watchfiles", "multipart"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # ── Uvicorn access log integration ───────────────────────────────
    # Make uvicorn use the same handlers as root logger
    for uv_name in ("uvicorn", "uvicorn.access", "uvicorn.error"):
        uv_logger = logging.getLogger(uv_name)
        uv_logger.handlers.clear()
        uv_logger.propagate = True

    # ── Startup banner ───────────────────────────────────────────────
    logger = logging.getLogger("app.core.logging_config")
    logger.info("=" * 70)
    logger.info("Logging initialized - level=%s dir=%s sql=%s", log_level, log_path.resolve(), log_sql)
    logger.info("  Console : %s+ -> stdout (colored)", log_level)
    logger.info("  AppFile : %s+ -> %s (max %s MB × %d)", log_level, app_file, max_bytes // (1024 * 1024), backup_count)
    logger.info("  ErrFile : ERROR+ -> %s (max %s MB × %d)", error_file, max_bytes // (1024 * 1024), backup_count)
    logger.info("=" * 70)
