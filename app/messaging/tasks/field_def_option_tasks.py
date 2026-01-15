"""
Celery tasks for FieldDefOption domain events.

These handlers process FieldDefOption created, updated and deleted events.
They parse the incoming envelope or payload, propagate correlation
information and validate the message using the Pydantic event schemas.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from app.core.celery_app import celery_app
from app.domain.schemas.events.common import EventEnvelope
from app.domain.schemas.events.field_def_option_events import (
    FieldDefOptionCreatedMessage,
    FieldDefOptionUpdatedMessage,
    FieldDefOptionDeletedMessage,
)
from app.util.correlation import (
    set_correlation_id,
    set_message_id,
)
from app.core.telemetry import attach_current_span_context


logger = logging.getLogger(__name__)


def _parse_envelope(*, envelope: Dict[str, Any] | None, payload: Dict[str, Any] | None, task_name: str) -> EventEnvelope:
    """Construct or validate an EventEnvelope.

    Accepts either a full envelope or a legacy payload.  When only a payload
    is provided, a synthetic envelope is constructed with default values.
    """
    if envelope is None and payload is not None:
        tenant_id = payload.get("tenant_id")
        synthetic = {
            "event_id": uuid4(),
            "event_type": task_name,
            "schema_version": 1,
            "occurred_at": datetime.utcnow(),
            "producer": "schema-composition-service",
            "tenant_id": tenant_id,
            "correlation_id": None,
            "causation_id": None,
            "traceparent": None,
            "data": payload,
        }
        return EventEnvelope.model_validate(synthetic)
    return EventEnvelope.model_validate(envelope)


def _propagate_trace(event: EventEnvelope) -> None:
    """Propagate correlation context to the current worker span."""
    if event.correlation_id:
        set_correlation_id(str(event.correlation_id))
    set_message_id(str(event.event_id))
    try:
        attach_current_span_context(
            tenant_id=str(event.tenant_id) if event.tenant_id else None,
            correlation_id=str(event.correlation_id) if event.correlation_id else None,
            message_id=str(event.event_id),
        )
    except Exception:
        pass


@celery_app.task(
    name="SchemaComposition.field-def-option.created",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def handle_field_def_option_created(*, envelope: Dict[str, Any] | None = None, payload: Dict[str, Any] | None = None) -> None:
    """Handle a created FieldDefOption event."""
    event = _parse_envelope(envelope=envelope, payload=payload, task_name="SchemaComposition.field-def-option.created")
    _propagate_trace(event)
    message = FieldDefOptionCreatedMessage.model_validate(event.data)
    logger.info(
        "FieldDefOption created",
        extra={
            "tenant_id": str(message.tenant_id),
            "field_def_option_id": str(message.field_def_option_id),
            "field_def_id": str(message.field_def_id),
            "message_id": str(event.event_id),
            "correlation_id": str(event.correlation_id) if event.correlation_id else None,
        },
    )


@celery_app.task(
    name="SchemaComposition.field-def-option.updated",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def handle_field_def_option_updated(*, envelope: Dict[str, Any] | None = None, payload: Dict[str, Any] | None = None) -> None:
    """Handle an updated FieldDefOption event."""
    event = _parse_envelope(envelope=envelope, payload=payload, task_name="SchemaComposition.field-def-option.updated")
    _propagate_trace(event)
    message = FieldDefOptionUpdatedMessage.model_validate(event.data)
    logger.info(
        "FieldDefOption updated",
        extra={
            "tenant_id": str(message.tenant_id),
            "field_def_option_id": str(message.field_def_option_id),
            "field_def_id": str(message.field_def_id),
            "changed_fields": list(message.changes.keys()),
            "message_id": str(event.event_id),
            "correlation_id": str(event.correlation_id) if event.correlation_id else None,
        },
    )


@celery_app.task(
    name="SchemaComposition.field-def-option.deleted",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def handle_field_def_option_deleted(*, envelope: Dict[str, Any] | None = None, payload: Dict[str, Any] | None = None) -> None:
    """Handle a deleted FieldDefOption event."""
    event = _parse_envelope(envelope=envelope, payload=payload, task_name="SchemaComposition.field-def-option.deleted")
    _propagate_trace(event)
    message = FieldDefOptionDeletedMessage.model_validate(event.data)
    logger.info(
        "FieldDefOption deleted",
        extra={
            "tenant_id": str(message.tenant_id),
            "field_def_option_id": str(message.field_def_option_id),
            "field_def_id": str(message.field_def_id),
            "message_id": str(event.event_id),
            "correlation_id": str(event.correlation_id) if event.correlation_id else None,
        },
    )