"""
Utilities for managing correlation and causation identifiers across
asynchronous workflows. By storing identifiers in context variables,
code can propagate and access these values without passing them
explicitly through every function call. Use ``get_correlation_id``
and ``set_correlation_id`` to manage the current correlation ID
throughout a request or message processing cycle. Similarly,
``get_message_id`` and ``set_message_id`` track the current message
identifier for causation tracking.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Optional
from uuid import uuid4
import logging

try:
    # Attempt to import OpenTelemetry trace API.  If tracing is not
    # installed, this will fail and trace will be None.  We do not
    # import instrumentation packages here.
    from opentelemetry import trace  # type: ignore
except Exception:  # pragma: no cover
    trace = None  # type: ignore

logger = logging.getLogger(__name__)


_correlation_id: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)
_message_id: ContextVar[Optional[str]] = ContextVar("message_id", default=None)


def get_correlation_id() -> str:
    """Return the current correlation ID, generating one if absent."""
    cid = _correlation_id.get()
    if cid is None:
        cid = str(uuid4())
        _correlation_id.set(cid)
    return cid


def set_correlation_id(cid: Optional[str]) -> None:
    """Set the correlation ID for the current context."""
    if cid:
        _correlation_id.set(cid)
        # Attach correlation_id to current span if tracing is active
        try:
            if trace is not None:
                span = trace.get_current_span()
                # Only set attribute if span implements set_attribute (no-op span may not)
                if span and hasattr(span, "set_attribute"):
                    span.set_attribute("dyno.correlation_id", cid)
        except Exception:
            # Logging at debug level to avoid polluting logs on failure
            logger.debug("Could not attach correlation_id to span", exc_info=True)


def get_message_id() -> Optional[str]:
    """Get the current message ID (causation ID)."""
    return _message_id.get()


def set_message_id(mid: str) -> None:
    """Set the message ID for the current context."""
    _message_id.set(mid)
    # Attach message_id to current span if tracing is active
    try:
        if trace is not None:
            span = trace.get_current_span()
            if span and hasattr(span, "set_attribute"):
                span.set_attribute("dyno.message_id", mid)
    except Exception:
        logger.debug("Could not attach message_id to span", exc_info=True)