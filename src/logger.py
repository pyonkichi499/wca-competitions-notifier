"""Logging configuration for the WCA Kanto Notifier."""

import json
import logging
import os
import sys
from datetime import datetime, timezone

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Cloud Run sets K_SERVICE automatically
IS_CLOUD_RUN = os.getenv("K_SERVICE") is not None


class CloudRunJsonFormatter(logging.Formatter):
    """JSON formatter for Cloud Logging integration.

    Cloud Run automatically ingests structured logs from stdout.
    See: https://cloud.google.com/run/docs/logging#writing_structured_logs
    """

    SEVERITY_MAP = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON for Cloud Logging."""
        log_entry = {
            "severity": self.SEVERITY_MAP.get(record.levelno, "DEFAULT"),
            "message": record.getMessage(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "logging.googleapis.com/sourceLocation": {
                "file": record.pathname,
                "line": record.lineno,
                "function": record.funcName,
            },
            "logger": record.name,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


class LocalFormatter(logging.Formatter):
    """Human-readable formatter for local development."""

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def setup_logging(level: str | None = None) -> None:
    """Configure logging for the application.

    Automatically detects environment:
    - Cloud Run: JSON structured logs for Cloud Logging
    - Local: Human-readable text logs

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). Defaults to env var or INFO.
    """
    log_level = level or LOG_LEVEL

    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Create handler with appropriate formatter
    handler = logging.StreamHandler(sys.stdout)

    if IS_CLOUD_RUN:
        handler.setFormatter(CloudRunJsonFormatter())
    else:
        handler.setFormatter(LocalFormatter())

    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)
