"""Structured logging configuration using structlog.

Configures JSON-formatted structured logging with correlation ID propagation.
Every log line carries a correlation ID for request tracing across services.
"""

from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar

import structlog

# Context variable for correlation ID propagation across async tasks
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """Retrieve the current correlation ID, generating one if not set.

    Returns:
        str: The correlation ID for the current context.
    """
    cid = correlation_id_var.get()
    if not cid:
        cid = uuid.uuid4().hex
        correlation_id_var.set(cid)
    return cid


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for the current context.

    Args:
        correlation_id: The correlation ID to propagate through logs.
    """
    correlation_id_var.set(correlation_id)


def add_correlation_id(
    logger: structlog.types.WrappedLogger,
    method_name: str,
    event_dict: structlog.types.EventDict,
) -> structlog.types.EventDict:
    """Structlog processor that injects the correlation ID into every log entry.

    Args:
        logger: The wrapped logger instance.
        method_name: The name of the log method called.
        event_dict: The event dictionary being built.

    Returns:
        structlog.types.EventDict: The event dictionary with correlation_id added.
    """
    event_dict["correlation_id"] = get_correlation_id()
    return event_dict


def configure_logging(log_level: str = "INFO", log_format: str = "json") -> None:
    """Configure structlog and standard logging for the application.

    Args:
        log_level: The minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: Output format — 'json' for structured JSON, 'console' for human-readable.
    """
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        add_correlation_id,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if log_format == "json":
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.UnicodeDecoder(),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Also configure standard library logging for third-party libraries
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
