"""
Celery tasks for FieldDef domain events.

This module defines asynchronous handlers for FieldDef events published
by the API layer.  Each handler accepts either a fully populated
``EventEnvelope`` or a legacy ``payload`` dictionary and logs the
event details.  In a real system you might perform additional side
effects here, such as updating projection tables or invoking
external services.  When adding a new domain object copy this file
and adjust the task names, schema imports and side effects accordingly.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from app.core.celery_app import celery_app
from app.core.db import get_cm_db  # optional if you need DB access in tasks
from app.domain.schemas.events.common import EventEnvelope
from app.domain.schemas.events.field_def_events import (
    FieldDefCreatedMessage,
    FieldDefUpdatedMessage,
    FieldDefDeletedMessage,
)
from app.util.correlation import (
    set_correlation_id,
    set_message_id,
    get_correlation_id,
    get_message_id,
)
from app.core.telemetry import attach_current_span_context


logger = logging.getLogger(__name__)


def _parse_envelope(*, envelope: Dict[str, Any] | None, payload: Dict[str, Any] | None, task_name: str) -> EventEnvelope:
    """Helper to build or validate an EventEnvelope.

    Accepts either a full envelope or a legacy payload.  When only a
    payload is provided, a synthetic envelope is constructed with a
    new event_id and occurred_at timestamp.  The schema_version is
    defaulted to 1 and the producer is assumed to be this service.
    """
    if envelope is None and payload is not None:
        tenant_id = payload.get("tenant_id")
        synthetic = {
            "event_id": uuid4(),
            "event_type": task_name,
            "schema_version": 1,
            "occurred_at": datetime.utcnow(),
            "producer": "my-entity-service",
            "tenant_id": tenant_id,
            "correlation_id": None,
            "causation_id": None,
            "traceparent": None,
            "data": payload,
        }
        return EventEnvelope.model_validate(synthetic)
    # Validate existing envelope
    return EventEnvelope.model_validate(envelope)


def _propagate_trace(event: EventEnvelope) -> None:
    """Propagate correlation context to the current worker span."""
    if event.correlation_id:
        set_correlation_id(str(event.correlation_id))
    # Always set message_id as the causation identifier for downstream events
    set_message_id(str(event.event_id))
    try:
        attach_current_span_context(
            tenant_id=str(event.tenant_id) if event.tenant_id else None,
            correlation_id=str(event.correlation_id) if event.correlation_id else None,
            message_id=str(event.event_id),
        )
    except Exception:
        # Failing to attach trace context should not block processing
        pass


@celery_app.task(
    name="conversa.field-def.created",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def handle_field_def_created(*, envelope: Dict[str, Any] | None = None, payload: Dict[str, Any] | None = None) -> None:
    """Handle a newly created FieldDef event.

    Logs the event details.  In a real application you could update
    derived read models or trigger downstream workflows here.
    """
    event = _parse_envelope(envelope=envelope, payload=payload, task_name="conversa.field-def.created")
    _propagate_trace(event)
    # Validate domain payload
    message = FieldDefCreatedMessage.model_validate(event.data)
    logger.info(
        "FieldDef created",
        extra={
            "tenant_id": str(message.tenant_id),
            "field_def_id": str(message.field_def_id),
            "message_id": str(event.event_id),
            "correlation_id": str(event.correlation_id) if event.correlation_id else None,
        },
    )


@celery_app.task(
    name="conversa.field-def.updated",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def handle_field_def_updated(*, envelope: Dict[str, Any] | None = None, payload: Dict[str, Any] | None = None) -> None:
    """Handle an updated FieldDef event."""
    event = _parse_envelope(envelope=envelope, payload=payload, task_name="conversa.field-def.updated")
    _propagate_trace(event)
    message = FieldDefUpdatedMessage.model_validate(event.data)
    logger.info(
        "FieldDef updated",
        extra={
            "tenant_id": str(message.tenant_id),
            "field_def_id": str(message.field_def_id),
            "changed_fields": list(message.changes.keys()),
            "message_id": str(event.event_id),
            "correlation_id": str(event.correlation_id) if event.correlation_id else None,
        },
    )


@celery_app.task(
    name="conversa.field-def.deleted",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def handle_field_def_deleted(*, envelope: Dict[str, Any] | None = None, payload: Dict[str, Any] | None = None) -> None:
    """Handle a deleted FieldDef event."""
    event = _parse_envelope(envelope=envelope, payload=payload, task_name="conversa.field-def.deleted")
    _propagate_trace(event)
    message = FieldDefDeletedMessage.model_validate(event.data)
    logger.info(
        "FieldDef deleted",
        extra={
            "tenant_id": str(message.tenant_id),
            "field_def_id": str(message.field_def_id),
            "deleted_dt": message.deleted_dt,
            "message_id": str(event.event_id),
            "correlation_id": str(event.correlation_id) if event.correlation_id else None,
        },
    )