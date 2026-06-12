"""
CheckPoint — Logging system.

Provides a centralized, configured logger with rotating file output
and console output. All application modules should import get_logger()
to obtain a child logger.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from app.utils.paths import get_logs_dir


_initialized: bool = False
_root_logger_name: str = "checkpoint"


def setup_logging(level: str = "INFO", max_bytes: int = 5_242_880,
                  backup_count: int = 3) -> None:
    """
    Initialize the application logging system.

    Creates a rotating file handler and a console handler on the
    'checkpoint' root logger. Safe to call multiple times; subsequent
    calls are no-ops.

    Args:
        level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        max_bytes: Maximum size of each log file before rotation.
        backup_count: Number of rotated log files to keep.
    """
    global _initialized
    if _initialized:
        return

    log_dir = get_logs_dir()
    log_file = log_dir / "checkpoint.log"

    logger = logging.getLogger(_root_logger_name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Formatter
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_file),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    _initialized = True
    logger.info("Logging system initialized — level=%s, file=%s", level, log_file)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a logger instance scoped under the checkpoint namespace.

    Args:
        name: Optional sub-module name. If provided, the logger name
              becomes 'checkpoint.<name>'.

    Returns:
        A configured logging.Logger instance.
    """
    if name:
        return logging.getLogger(f"{_root_logger_name}.{name}")
    return logging.getLogger(_root_logger_name)
