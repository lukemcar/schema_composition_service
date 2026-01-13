"""
Celery tasks for ComponentPanelField domain events.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from app.core.celery_app import celery_app
from app.domain.schemas.events.common import EventEnvelope
from app.domain.schemas.events.component_panel_field_events import (
    ComponentPanelFieldCreatedMessage,
    ComponentPanelFieldUpdatedMessage,
    ComponentPanelFieldDeletedMessage,
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
            "producer": "my-entity-service",
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
    name="conversa.component-panel-field.created",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def handle_component_panel_field_created(*, envelope: Dict[str, Any] | None = None, payload: Dict[str, Any] | None = None) -> None:
    event = _parse_envelope(
        envelope=envelope, payload=payload, task_name="conversa.component-panel-field.created"
    )
    _propagate_trace(event)
    message = ComponentPanelFieldCreatedMessage.model_validate(event.data)
    logger.info(
        "ComponentPanelField created",
        extra={
            "tenant_id": str(message.tenant_id),
            "component_panel_field_id": str(message.component_panel_field_id),
            "component_panel_id": str(message.component_panel_id),
            "field_def_id": str(message.field_def_id),
            "message_id": str(event.event_id),
            "correlation_id": str(event.correlation_id) if event.correlation_id else None,
        },
    )


@celery_app.task(
    name="conversa.component-panel-field.updated",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def handle_component_panel_field_updated(*, envelope: Dict[str, Any] | None = None, payload: Dict[str, Any] | None = None) -> None:
    event = _parse_envelope(
        envelope=envelope, payload=payload, task_name="conversa.component-panel-field.updated"
    )
    _propagate_trace(event)
    message = ComponentPanelFieldUpdatedMessage.model_validate(event.data)
    logger.info(
        "ComponentPanelField updated",
        extra={
            "tenant_id": str(message.tenant_id),
            "component_panel_field_id": str(message.component_panel_field_id),
            "component_panel_id": str(message.component_panel_id),
            "field_def_id": str(message.field_def_id),
            "changed_fields": list(message.changes.keys()),
            "message_id": str(event.event_id),
            "correlation_id": str(event.correlation_id) if event.correlation_id else None,
        },
    )


@celery_app.task(
    name="conversa.component-panel-field.deleted",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=3,
    acks_late=True,
)
def handle_component_panel_field_deleted(*, envelope: Dict[str, Any] | None = None, payload: Dict[str, Any] | None = None) -> None:
    event = _parse_envelope(
        envelope=envelope, payload=payload, task_name="conversa.component-panel-field.deleted"
    )
    _propagate_trace(event)
    message = ComponentPanelFieldDeletedMessage.model_validate(event.data)
    logger.info(
        "ComponentPanelField deleted",
        extra={
            "tenant_id": str(message.tenant_id),
            "component_panel_field_id": str(message.component_panel_field_id),
            "component_panel_id": str(message.component_panel_id),
            "field_def_id": str(message.field_def_id),
            "message_id": str(event.event_id),
            "correlation_id": str(event.correlation_id) if event.correlation_id else None,
        },
    )