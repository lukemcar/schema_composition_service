"""
Celery producer for ComponentPanelField events.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import celery_app
from app.domain.schemas.events import (
    ComponentPanelFieldCreatedMessage,
    ComponentPanelFieldUpdatedMessage,
    ComponentPanelFieldDeletedMessage,
)
from app.domain.schemas.events.common import EventEnvelope
from app.util.correlation import get_correlation_id, get_message_id


class ComponentPanelFieldProducer:
    """Publish ComponentPanelField lifecycle events."""

    @staticmethod
    def _build_headers() -> Dict[str, str]:
        return {
            "correlation_id": get_correlation_id() or "",
            "message_id": get_message_id() or "",
        }

    @staticmethod
    def send_component_panel_field_created(
        *,
        tenant_id: UUID,
        component_panel_field_id: UUID,
        component_panel_id: UUID,
        field_def_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = ComponentPanelFieldCreatedMessage(
            tenant_id=tenant_id,
            component_panel_field_id=component_panel_field_id,
            component_panel_id=component_panel_id,
            field_def_id=field_def_id,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), ComponentPanelFieldCreatedMessage)
        celery_app.send_task(
            "SchemaComposition.component-panel-field.created",
            args=[envelope.model_dump(mode="json")],
            headers=ComponentPanelFieldProducer._build_headers(),
        )

    @staticmethod
    def send_component_panel_field_updated(
        *,
        tenant_id: UUID,
        component_panel_field_id: UUID,
        component_panel_id: UUID,
        field_def_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        message = ComponentPanelFieldUpdatedMessage(
            tenant_id=tenant_id,
            component_panel_field_id=component_panel_field_id,
            component_panel_id=component_panel_id,
            field_def_id=field_def_id,
            changes=changes,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), ComponentPanelFieldUpdatedMessage)
        celery_app.send_task(
            "SchemaComposition.component-panel-field.updated",
            args=[envelope.model_dump(mode="json")],
            headers=ComponentPanelFieldProducer._build_headers(),
        )

    @staticmethod
    def send_component_panel_field_deleted(
        *,
        tenant_id: UUID,
        component_panel_field_id: UUID,
        component_panel_id: UUID,
        field_def_id: UUID,
    ) -> None:
        message = ComponentPanelFieldDeletedMessage(
            tenant_id=tenant_id,
            component_panel_field_id=component_panel_field_id,
            component_panel_id=component_panel_id,
            field_def_id=field_def_id,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), ComponentPanelFieldDeletedMessage)
        celery_app.send_task(
            "SchemaComposition.component-panel-field.deleted",
            args=[envelope.model_dump(mode="json")],
            headers=ComponentPanelFieldProducer._build_headers(),
        )