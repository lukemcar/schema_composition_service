"""
Producer for MyEntity domain events.

This module defines a simple producer class for publishing MyEntity
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
from app.domain.schemas.events.my_entity_events import (
    MyEntityCreatedMessage,
    MyEntityUpdatedMessage,
    MyEntityDeletedMessage,
)
from app.domain.schemas.events.common import EventEnvelope
from app.util.correlation import (
    get_correlation_id,
    get_message_id,
    set_message_id,
)


class MyEntityProducer:
    """Publishes MyEntity events via Celery.

    The task names double as routing keys on the ``conversa`` exchange.
    They follow the naming convention ``conversa.<domain>.<event>`` to
    enable fine‑grained routing by queue bindings.  When creating a new
    producer for your domain follow this pattern and ensure the Celery
    configuration defines matching routes.
    """

    TASK_CREATED = "conversa.my-entity.created"
    TASK_UPDATED = "conversa.my-entity.updated"
    TASK_DELETED = "conversa.my-entity.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID, my_entity_id: UUID) -> Dict[str, str]:
        """Construct message headers with identifiers for traceability.

        Headers are optional metadata that accompany the message and
        allow consumers to quickly access key identifiers without
        inspecting the payload.  Include tenant and entity IDs here.
        """
        return {
            "tenant_id": str(tenant_id),
            "my_entity_id": str(my_entity_id),
        }

    @classmethod
    def _send(
        cls,
        *,
        task_name: str,
        message_model: Any,
        headers: Dict[str, str],
    ) -> None:
        """Internal helper: wrap the domain message in an EventEnvelope and send it.

        The envelope captures metadata such as event identifiers,
        correlation/causation IDs and timestamps.  The Celery task name is
        used both as the ``event_type`` and the routing key.
        """
        payload = message_model.model_dump(mode="json")
        envelope = EventEnvelope(
            event_id=uuid4(),
            event_type=task_name,
            schema_version=1,
            occurred_at=datetime.utcnow(),
            producer="my-entity-service",
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
    def send_my_entity_created(
        cls,
        *,
        tenant_id: UUID,
        my_entity_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ``my-entity.created`` event.

        Args:
            tenant_id: The tenant that owns the entity.
            my_entity_id: The primary key of the created entity.
            payload: The full entity state to include in the event body.
        """
        message = MyEntityCreatedMessage(
            tenant_id=tenant_id,
            my_entity_id=my_entity_id,
            payload=payload,
        )
        headers = cls._build_headers(
            tenant_id=tenant_id,
            my_entity_id=my_entity_id,
        )
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_my_entity_updated(
        cls,
        *,
        tenant_id: UUID,
        my_entity_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ``my-entity.updated`` event.

        Args:
            tenant_id: Tenant owning the entity.
            my_entity_id: Identifier of the updated entity.
            changes: A dictionary of fields that were modified.
            payload: The full updated entity state.
        """
        message = MyEntityUpdatedMessage(
            tenant_id=tenant_id,
            my_entity_id=my_entity_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(
            tenant_id=tenant_id,
            my_entity_id=my_entity_id,
        )
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_my_entity_deleted(
        cls,
        *,
        tenant_id: UUID,
        my_entity_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a ``my-entity.deleted`` event.

        Args:
            tenant_id: Tenant owning the entity.
            my_entity_id: Identifier of the deleted entity.
            deleted_dt: Optional ISO‑formatted deletion timestamp.  If
                not provided the consumer may use its own timestamp.
        """
        message = MyEntityDeletedMessage(
            tenant_id=tenant_id,
            my_entity_id=my_entity_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(
            tenant_id=tenant_id,
            my_entity_id=my_entity_id,
        )
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)
