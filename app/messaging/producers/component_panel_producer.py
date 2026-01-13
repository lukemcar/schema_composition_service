"""
Celery producer for ComponentPanel events.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import celery_app
from app.domain.schemas.events import (
    ComponentPanelCreatedMessage,
    ComponentPanelUpdatedMessage,
    ComponentPanelDeletedMessage,
)
from app.domain.schemas.events.common import EventEnvelope
from app.util.correlation import get_correlation_id, get_message_id


class ComponentPanelProducer:
    """Publish ComponentPanel lifecycle events via Celery."""

    @staticmethod
    def _build_headers() -> Dict[str, str]:
        return {
            "correlation_id": get_correlation_id() or "",
            "message_id": get_message_id() or "",
        }

    @staticmethod
    def send_component_panel_created(
        *, tenant_id: UUID, component_panel_id: UUID, component_id: UUID, payload: Dict[str, Any]
    ) -> None:
        message = ComponentPanelCreatedMessage(
            tenant_id=tenant_id,
            component_panel_id=component_panel_id,
            component_id=component_id,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), ComponentPanelCreatedMessage)
        celery_app.send_task(
            "conversa.component-panel.created",
            args=[envelope.model_dump(mode="json")],
            headers=ComponentPanelProducer._build_headers(),
        )

    @staticmethod
    def send_component_panel_updated(
        *,
        tenant_id: UUID,
        component_panel_id: UUID,
        component_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        message = ComponentPanelUpdatedMessage(
            tenant_id=tenant_id,
            component_panel_id=component_panel_id,
            component_id=component_id,
            changes=changes,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), ComponentPanelUpdatedMessage)
        celery_app.send_task(
            "conversa.component-panel.updated",
            args=[envelope.model_dump(mode="json")],
            headers=ComponentPanelProducer._build_headers(),
        )

    @staticmethod
    def send_component_panel_deleted(
        *, tenant_id: UUID, component_panel_id: UUID, component_id: UUID
    ) -> None:
        message = ComponentPanelDeletedMessage(
            tenant_id=tenant_id,
            component_panel_id=component_panel_id,
            component_id=component_id,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), ComponentPanelDeletedMessage)
        celery_app.send_task(
            "conversa.component-panel.deleted",
            args=[envelope.model_dump(mode="json")],
            headers=ComponentPanelProducer._build_headers(),
        )