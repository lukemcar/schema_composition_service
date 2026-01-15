"""
Centralised JSON logging for the SchemaComposition microservice.

This module configures Python's :mod:`logging` module to emit
structured JSON log lines enriched with OpenTelemetry trace context.  The
configuration is applied once on application and worker startup via
the :func:`configure_logging` function.  A legacy wrapper
:func:`setup_logging` is retained for backward compatibility with
existing imports.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict

try:
    # Attempt to import OpenTelemetry context API.  If unavailable,
    # tracing fields will be omitted from logs.
    from opentelemetry import trace  # type: ignore
except Exception:
    trace = None  # type: ignore


class JsonLogFormatter(logging.Formatter):
    """Custom log formatter that emits structured JSON.

    Each log record is serialised to a JSON object with at least the
    following fields:

      - ``timestamp``: ISO 8601 timestamp with UTC timezone
      - ``level``: log level name
      - ``name``: logger name
      - ``message``: formatted message
      - ``trace_id``: current OpenTelemetry trace id (hex), if available
      - ``span_id``: current span id (hex), if available
      - ``request_id``: a user-defined correlation id if supplied on
        the record (set via logger.bind or ``extra`` dict)
      - ``entrypoint`` / ``task_name``: when running inside a Celery
        worker, tasks may attach these fields via ``extra``

    Additional attributes attached to the record via ``extra`` will be
    preserved in the JSON output.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {}
        # Timestamp in ISO 8601 with timezone
        log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"
        log_record["level"] = record.levelname
        log_record["name"] = record.name
        log_record["message"] = record.getMessage()
        # Trace context
        if trace is not None:
            span = trace.get_current_span()
            ctx = span.get_span_context() if span is not None else None
            if ctx and ctx.trace_id != 0:
                # format trace_id and span_id as 32/16 hex digits
                log_record["trace_id"] = format(ctx.trace_id, "032x")
                log_record["span_id"] = format(ctx.span_id, "016x")
        # Correlation / request id
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        # entrypoint and task_name for Celery workers
        for field in ("entrypoint", "task_name"):
            if hasattr(record, field):
                log_record[field] = getattr(record, field)
        # Preserve any user-defined extras
        for key, value in record.__dict__.items():
            if key not in {
                "args",
                "asctime",
                "created",
                "exc_info",
                "exc_text",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "msg",
                "name",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "thread",
                "threadName",
            }:
                # Do not overwrite existing keys
                if key not in log_record:
                    log_record[key] = value
        # Serialise to JSON
        try:
            return json.dumps(log_record, default=str)
        except Exception:
            # Fallback to plain message on failure
            return json.dumps({"message": record.getMessage()})


def configure_logging() -> logging.Logger:
    """Configure the root logger for JSON output.

    Returns a named logger for the application.  This function may be
    called multiple times but will only configure the root handlers on
    first invocation.  The log level is derived from the ``LOG_LEVEL``
    environment variable (default ``INFO``).
    """
    # Determine log level from environment
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level_str, logging.INFO)
    root_logger = logging.getLogger()
    # If handlers already configured, do not duplicate
    if not root_logger.handlers:
        handler = logging.StreamHandler()
        formatter = JsonLogFormatter()
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)
        root_logger.setLevel(level)
    # Return a dedicated application logger
    return logging.getLogger("SchemaComposition")


# Backwards compatibility
def setup_logging() -> logging.Logger:
    """Alias for :func:`configure_logging`.  Retained for legacy imports."""
    return configure_logging()

def get_logger(name:str):
    return logging.getLogger(name)
