"""
Structured logging setup for the STMS application.
Features:
- Handler de-duplication across reload events
- Injected request_id from ContextVar
- Automatic redaction of sensitive credentials, secrets, tokens, and passwords
"""
import logging
import re
import sys

from app.config import get_settings

SENSITIVE_PATTERNS = [
    (re.compile(r'(password[\'"]?\s*[:=]\s*[\'"])([^\'"]+)([\'"])', re.IGNORECASE), r'\1***REDACTED***\3'),
    (re.compile(r'(token[\'"]?\s*[:=]\s*[\'"])([^\'"]+)([\'"])', re.IGNORECASE), r'\1***REDACTED***\3'),
    (re.compile(r'(secret[\'"]?\s*[:=]\s*[\'"])([^\'"]+)([\'"])', re.IGNORECASE), r'\1***REDACTED***\3'),
    (re.compile(r'(authorization[\'"]?\s*[:=]\s*[\'"]Bearer\s+)([^\'"]+)([\'"])', re.IGNORECASE), r'\1***REDACTED***\3'),
    (re.compile(r'(Bearer\s+)[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*', re.IGNORECASE), r'\1***REDACTED_JWT***'),
]


class RequestIDFilter(logging.Filter):
    """Injects current request ID from ContextVar into LogRecord."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from app.middleware.request_id import get_request_id
            record.request_id = get_request_id() or "-"
        except Exception:
            record.request_id = "-"
        return True


class SensitiveDataFilter(logging.Filter):
    """Redacts passwords, tokens, API keys, and Authorization headers from log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in SENSITIVE_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True


def setup_logging() -> logging.Logger:
    """
    Configure application-wide logging idempotently.
    Clears existing handlers to prevent duplication on server reloads.
    """
    settings = get_settings()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | [%(request_id)s] | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    req_filter = RequestIDFilter()
    redact_filter = SensitiveDataFilter()

    # Configure root application logger
    app_logger = logging.getLogger("stms")
    app_logger.setLevel(log_level)

    # Clear existing handlers to prevent duplication on reloads
    for handler in list(app_logger.handlers):
        app_logger.removeHandler(handler)

    # Console handler (always active)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(req_filter)
    console_handler.addFilter(redact_filter)
    app_logger.addHandler(console_handler)

    # File handler (logs/stms.log)
    log_dir = settings.root_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "stms.log", encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(req_filter)
    file_handler.addFilter(redact_filter)
    app_logger.addHandler(file_handler)

    # Prevent double-propagation to root
    app_logger.propagate = False

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("ultralytics").setLevel(logging.WARNING)

    return app_logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger under the 'stms' namespace."""
    return logging.getLogger(f"stms.{name}")
