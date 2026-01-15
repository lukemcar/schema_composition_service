"""
Celery tasks for Component domain events.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from app.core.celery_app import celery_app
from app.domain.schemas.events.common import EventEnvelope
from app.domain.schemas.events.component_events import (
    ComponentCreatedMessage,
    ComponentUpdatedMessage,
    ComponentDeletedMessage,
)
from app.util.correlation import set_correlation_id, set_message_id
from app.core.telemetry import attach_current_span_context

logger = logging.getLogger(__name__)


def _parse_envelope(*, envelope: Dict[str, Any] | None, payload: Dict[str, Any] | None, task_name: str) -> EventEnvelope:
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
    name="SchemaComposition.component.created",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def handle_component_created(*, envelope: Dict[str, Any] | None = None, payload: Dict[str, Any] | None = None) -> None:
    event = _parse_envelope(envelope=envelope, payload=payload, task_name="SchemaComposition.component.created")
    _propagate_trace(event)
    message = ComponentCreatedMessage.model_validate(event.data)
    logger.info(
        "Component created",
        extra={
            "tenant_id": str(message.tenant_id),
            "component_id": str(message.component_id),
            "message_id": str(event.event_id),
            "correlation_id": str(event.correlation_id) if event.correlation_id else None,
        },
    )


@celery_app.task(
    name="SchemaComposition.component.updated",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def handle_component_updated(*, envelope: Dict[str, Any] | None = None, payload: Dict[str, Any] | None = None) -> None:
    event = _parse_envelope(envelope=envelope, payload=payload, task_name="SchemaComposition.component.updated")
    _propagate_trace(event)
    message = ComponentUpdatedMessage.model_validate(event.data)
    logger.info(
        "Component updated",
        extra={
            "tenant_id": str(message.tenant_id),
            "component_id": str(message.component_id),
            "changed_fields": list(message.changes.keys()),
            "message_id": str(event.event_id),
            "correlation_id": str(event.correlation_id) if event.correlation_id else None,
        },
    )


@celery_app.task(
    name="SchemaComposition.component.deleted",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def handle_component_deleted(*, envelope: Dict[str, Any] | None = None, payload: Dict[str, Any] | None = None) -> None:
    event = _parse_envelope(envelope=envelope, payload=payload, task_name="SchemaComposition.component.deleted")
    _propagate_trace(event)
    message = ComponentDeletedMessage.model_validate(event.data)
    logger.info(
        "Component deleted",
        extra={
            "tenant_id": str(message.tenant_id),
            "component_id": str(message.component_id),
            "message_id": str(event.event_id),
            "correlation_id": str(event.correlation_id) if event.correlation_id else None,
        },
    )