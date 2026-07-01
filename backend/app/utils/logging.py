"""
Structured logging setup for the STMS application.
Replaces scattered print() calls with proper logging.
"""
import logging
import sys
from pathlib import Path

from app.config import get_settings


def setup_logging() -> logging.Logger:
    """
    Configure application-wide logging.

    Returns the root application logger.
    """
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (always active)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    # File handler (logs/ directory)
    log_dir = settings.root_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "stms.log", encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    # Configure root logger for the app
    app_logger = logging.getLogger("stms")
    app_logger.setLevel(log_level)
    app_logger.addHandler(console_handler)
    app_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("ultralytics").setLevel(logging.WARNING)

    return app_logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under the 'stms' namespace."""
    return logging.getLogger(f"stms.{name}")
