"""
Producer for FieldDef domain events.

This module defines a producer class for publishing FieldDef
lifecycle events via Celery/RabbitMQ.  Each method wraps the
corresponding domain payload in an ``EventEnvelope`` and sends it
through the shared Celery application.  When adding a new domain
object copy this producer and adjust the task names, headers and
payload models accordingly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4

from app.core.celery_app import celery_app
from app.domain.schemas.events.field_def_events import (
    FieldDefCreatedMessage,
    FieldDefUpdatedMessage,
    FieldDefDeletedMessage,
)
from app.domain.schemas.events.common import EventEnvelope
from app.util.correlation import (
    get_correlation_id,
    get_message_id,
    set_message_id,
)


class FieldDefProducer:
    """Publishes FieldDef events via Celery.

    The task names double as routing keys on the ``SchemaComposition`` exchange.
    They follow the naming convention ``SchemaComposition.field-def.<event>`` to
    enable fine‑grained routing by queue bindings.  When creating a new
    producer for your domain follow this pattern and ensure the Celery
    configuration defines matching routes.
    """

    TASK_CREATED = "SchemaComposition.field-def.created"
    TASK_UPDATED = "SchemaComposition.field-def.updated"
    TASK_DELETED = "SchemaComposition.field-def.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID, field_def_id: UUID) -> Dict[str, str]:
        """Construct message headers with identifiers for traceability."""
        return {
            "tenant_id": str(tenant_id),
            "field_def_id": str(field_def_id),
        }

    @classmethod
    def _send(
        cls,
        *,
        task_name: str,
        message_model: Any,
        headers: Dict[str, str],
    ) -> None:
        """Internal helper: wrap the domain message in an EventEnvelope and send it."""
        payload = message_model.model_dump(mode="json")
        envelope = EventEnvelope(
            event_id=uuid4(),
            event_type=task_name,
            schema_version=1,
            occurred_at=datetime.utcnow(),
            producer="schema-composition-service",
            tenant_id=message_model.tenant_id,
            correlation_id=get_correlation_id(),
            causation_id=get_message_id(),
            traceparent=None,
            data=payload,
        )
        # Set the new event_id as the causation ID for any downstream events
        set_message_id(str(envelope.event_id))
        correlation_headers = {
            "message_id": str(envelope.event_id),
            "correlation_id": str(envelope.correlation_id)
            if envelope.correlation_id is not None
            else None,
            "causation_id": str(envelope.causation_id)
            if envelope.causation_id is not None
            else None,
        }
        correlation_headers = {k: v for k, v in correlation_headers.items() if v}
        combined_headers = {**headers, **correlation_headers}
        celery_app.send_task(
            name=task_name,
            kwargs={"envelope": envelope.model_dump(mode="json")},
            headers=combined_headers,
        )

    @classmethod
    def send_field_def_created(
        cls,
        *,
        tenant_id: UUID,
        field_def_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ``field-def.created`` event."""
        message = FieldDefCreatedMessage(
            tenant_id=tenant_id,
            field_def_id=field_def_id,
            payload=payload,
        )
        headers = cls._build_headers(
            tenant_id=tenant_id, field_def_id=field_def_id
        )
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_field_def_updated(
        cls,
        *,
        tenant_id: UUID,
        field_def_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ``field-def.updated`` event."""
        message = FieldDefUpdatedMessage(
            tenant_id=tenant_id,
            field_def_id=field_def_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(
            tenant_id=tenant_id, field_def_id=field_def_id
        )
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_field_def_deleted(
        cls,
        *,
        tenant_id: UUID,
        field_def_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a ``field-def.deleted`` event."""
        message = FieldDefDeletedMessage(
            tenant_id=tenant_id,
            field_def_id=field_def_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(
            tenant_id=tenant_id, field_def_id=field_def_id
        )
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)
