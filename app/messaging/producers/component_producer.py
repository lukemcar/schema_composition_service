"""
Celery producer for Component events.

Provides helper functions to publish created, updated and deleted
events for Components. Uses Celery tasks defined in the worker
configuration.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import celery_app
from app.domain.schemas.events import (
    ComponentCreatedMessage,
    ComponentUpdatedMessage,
    ComponentDeletedMessage,
)
from app.domain.schemas.events.common import EventEnvelope
from app.util.correlation import get_correlation_id, get_message_id


class ComponentProducer:
    """Publish Component lifecycle events via Celery."""

    @staticmethod
    def _build_headers() -> Dict[str, str]:
        return {
            "correlation_id": get_correlation_id() or "",
            "message_id": get_message_id() or "",
        }

    @staticmethod
    def send_component_created(*, tenant_id: UUID, component_id: UUID, payload: Dict[str, Any]) -> None:
        message = ComponentCreatedMessage(
            tenant_id=tenant_id,
            component_id=component_id,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), ComponentCreatedMessage)
        celery_app.send_task(
            "conversa.component.created",
            args=[envelope.model_dump(mode="json")],
            headers=ComponentProducer._build_headers(),
        )

    @staticmethod
    def send_component_updated(
        *, tenant_id: UUID, component_id: UUID, changes: Dict[str, Any], payload: Dict[str, Any]
    ) -> None:
        message = ComponentUpdatedMessage(
            tenant_id=tenant_id,
            component_id=component_id,
            changes=changes,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), ComponentUpdatedMessage)
        celery_app.send_task(
            "conversa.component.updated",
            args=[envelope.model_dump(mode="json")],
            headers=ComponentProducer._build_headers(),
        )

    @staticmethod
    def send_component_deleted(*, tenant_id: UUID, component_id: UUID) -> None:
        message = ComponentDeletedMessage(
            tenant_id=tenant_id,
            component_id=component_id,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), ComponentDeletedMessage)
        celery_app.send_task(
            "conversa.component.deleted",
            args=[envelope.model_dump(mode="json")],
            headers=ComponentProducer._build_headers(),
        )