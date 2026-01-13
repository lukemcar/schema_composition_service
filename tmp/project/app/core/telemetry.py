"""
OpenTelemetry instrumentation for Dyno Conversa.

This module configures distributed tracing for both the FastAPI
application and Celery background workers.  When instrumentation
packages are available they are initialised; otherwise, the functions
perform no-op.  The tracer uses an OTLP exporter by default and
can be configured via environment variables (``OTEL_EXPORTER_OTLP_ENDPOINT``,
``OTEL_EXPORTER_OTLP_HEADERS``, etc.).
"""

from __future__ import annotations

import logging
from typing import Any

try:
    from opentelemetry import trace
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.celery import CeleryInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    # Additional instrumentation packages for httpx and SQLAlchemy.
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
except Exception:
    trace = None
    FastAPIInstrumentor = None  # type: ignore
    CeleryInstrumentor = None  # type: ignore
    HTTPXClientInstrumentor = None  # type: ignore
    SQLAlchemyInstrumentor = None  # type: ignore

logger = logging.getLogger(__name__)


def init_tracing(service_name: str) -> None:
    """Initialise OpenTelemetry tracing.

    When OpenTelemetry packages are unavailable this function logs a
    message and returns immediately.  Otherwise, a global tracer provider
    with an OTLP exporter is configured.
    """
    if trace is None:
        logger.info("OpenTelemetry not available; tracing disabled")
        return
    # Always (re)configure the tracer provider.  If a provider is already set,
    # we intentionally replace it so that changes in OTEL_SERVICE_NAME take effect.
    # Choose the service name based on the environment first.  If
    # OTEL_SERVICE_NAME is defined, prefer it over the passed
    # service_name argument.  This prevents code from silently
    # overriding the service name configured via environment variables.
    import os

    env_service_name = os.getenv("OTEL_SERVICE_NAME")
    chosen_service_name = env_service_name or service_name

    # Create an empty default resource and merge our custom service
    # attribute onto it.  We avoid using Resource.get_default() since
    # some versions of the OpenTelemetry SDK do not provide it.  The
    # merge operation ensures any default attributes (if present) are
    # preserved alongside our service.name.
    default_resource = Resource.create()
    custom_resource = Resource.create({"service.name": chosen_service_name})
    resource = default_resource.merge(custom_resource)
    provider = TracerProvider(resource=resource)
    exporter: Any = None
    try:
        exporter = OTLPSpanExporter()
    except Exception:
        # Could not create OTLP exporter; fallback to simple logging exporter
        logger.warning("Failed to create OTLP exporter; tracing disabled")
        return
    processor = BatchSpanProcessor(exporter)
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    logger.info("OpenTelemetry tracing configured for %s", service_name)


def instrument_httpx() -> None:
    """Instrument httpx clients globally.

    When the httpx instrumentation package is available, calling this
    function will ensure that all httpx.Client and AsyncClient instances
    automatically create spans for outbound requests.  If the package is
    not available or tracing is disabled, this function will log and
    return without raising an exception.  This function should be
    invoked once at application start (both in API and worker
    processes).
    """
    if HTTPXClientInstrumentor is None:
        logger.warning("httpx instrumentation not available; skipping")
        return
    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("httpx globally instrumented for tracing")
    except Exception:
        logger.exception("Failed to instrument httpx; tracing for httpx disabled")


def instrument_sqlalchemy(engine: Any) -> None:
    """Instrument a SQLAlchemy engine for tracing.

    This helper wraps SQLAlchemy's execution engine so that each
    database query emits a span.  It must be called after the engine
    is created.  If instrumentation is unavailable or tracing is
    disabled, the function logs and returns without error.

    Args:
        engine: The SQLAlchemy engine instance to instrument.
    """
    if SQLAlchemyInstrumentor is None:
        logger.warning("SQLAlchemy instrumentation not available; skipping")
        return
    try:
        # SQLAlchemyInstrumentor only instruments once per engine; calling
        # multiple times is safe but has no effect.
        SQLAlchemyInstrumentor().instrument(engine=engine)
        logger.info("SQLAlchemy engine instrumented for tracing")
    except Exception:
        logger.exception("Failed to instrument SQLAlchemy engine; tracing disabled for DB")


def attach_current_span_context(
    *, tenant_id: str | None = None, correlation_id: str | None = None, message_id: str | None = None
) -> None:
    """Attach correlation identifiers to the current active span.

    This helper reads the current span from the tracer provider and
    attaches custom attributes for tenant, correlation and message IDs
    if a span is active.  It should be called after setting the
    correlation/message IDs via the correlation utilities.  If no span
    is active or tracing is disabled, the function is a no-op.

    Args:
        tenant_id: The tenant identifier associated with the operation.
        correlation_id: The current correlation ID.
        message_id: The current message (causation) ID.
    """
    try:
        # If tracing is not enabled, trace will be None
        if trace is None:
            return
        span = trace.get_current_span()
        # Only attach attributes if there is an active span (not NoOp span)
        if span and hasattr(span, "set_attribute"):
            if tenant_id:
                span.set_attribute("dyno.tenant_id", tenant_id)
            if correlation_id:
                span.set_attribute("dyno.correlation_id", correlation_id)
            if message_id:
                span.set_attribute("dyno.message_id", message_id)
    except Exception:
        # Never raise from context attachment; swallow errors
        logger.debug("Could not attach context to span", exc_info=True)


def instrument_fastapi(app: Any) -> None:
    """Instrument a FastAPI application for tracing.

    Should be called after initialising tracing.  If instrumentation is
    not available, logs a warning.  FastAPIInstrumentor will wrap
    routes so that incoming requests start new spans automatically.
    """
    if FastAPIInstrumentor is None:
        logger.warning("FastAPI instrumentation not available; skipping")
        return
    FastAPIInstrumentor().instrument_app(app, tracer_provider=trace.get_tracer_provider())
    logger.info("FastAPI application instrumented for tracing")


def instrument_celery(celery_app: Any) -> None:
    """Instrument a Celery application for tracing.

    When the celery instrumentation package is available, tasks will
    automatically propagate context and create spans around task
    execution.
    """
    if CeleryInstrumentor is None:
        logger.warning("Celery instrumentation not available; skipping")
        return
    CeleryInstrumentor().instrument()
    logger.info("Celery instrumented for tracing")