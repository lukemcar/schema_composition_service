"""
Celery producer for FormPanelComponent events.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import celery_app
from app.domain.schemas.events import (
    FormPanelComponentCreatedMessage,
    FormPanelComponentUpdatedMessage,
    FormPanelComponentDeletedMessage,
)
from app.domain.schemas.events.common import EventEnvelope
from app.util.correlation import get_correlation_id, get_message_id


class FormPanelComponentProducer:
    """Publish FormPanelComponent lifecycle events via Celery."""

    @staticmethod
    def _build_headers() -> Dict[str, str]:
        return {
            "correlation_id": get_correlation_id() or "",
            "message_id": get_message_id() or "",
        }

    @staticmethod
    def send_form_panel_component_created(
        *,
        tenant_id: UUID,
        form_panel_component_id: UUID,
        form_panel_id: UUID,
        component_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = FormPanelComponentCreatedMessage(
            tenant_id=tenant_id,
            form_panel_component_id=form_panel_component_id,
            form_panel_id=form_panel_id,
            component_id=component_id,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormPanelComponentCreatedMessage)
        celery_app.send_task(
            "conversa.form-panel-component.created",
            args=[envelope.model_dump(mode="json")],
            headers=FormPanelComponentProducer._build_headers(),
        )

    @staticmethod
    def send_form_panel_component_updated(
        *,
        tenant_id: UUID,
        form_panel_component_id: UUID,
        form_panel_id: UUID,
        component_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        message = FormPanelComponentUpdatedMessage(
            tenant_id=tenant_id,
            form_panel_component_id=form_panel_component_id,
            form_panel_id=form_panel_id,
            component_id=component_id,
            changes=changes,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormPanelComponentUpdatedMessage)
        celery_app.send_task(
            "conversa.form-panel-component.updated",
            args=[envelope.model_dump(mode="json")],
            headers=FormPanelComponentProducer._build_headers(),
        )

    @staticmethod
    def send_form_panel_component_deleted(
        *,
        tenant_id: UUID,
        form_panel_component_id: UUID,
        form_panel_id: UUID,
        component_id: UUID,
    ) -> None:
        message = FormPanelComponentDeletedMessage(
            tenant_id=tenant_id,
            form_panel_component_id=form_panel_component_id,
            form_panel_id=form_panel_id,
            component_id=component_id,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormPanelComponentDeletedMessage)
        celery_app.send_task(
            "conversa.form-panel-component.deleted",
            args=[envelope.model_dump(mode="json")],
            headers=FormPanelComponentProducer._build_headers(),
        )