"""
Celery producer for FormPanel events.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import celery_app
from app.domain.schemas.events import (
    FormPanelCreatedMessage,
    FormPanelUpdatedMessage,
    FormPanelDeletedMessage,
)
from app.domain.schemas.events.common import EventEnvelope
from app.util.correlation import get_correlation_id, get_message_id


class FormPanelProducer:
    """Publish FormPanel lifecycle events via Celery."""

    @staticmethod
    def _build_headers() -> Dict[str, str]:
        return {
            "correlation_id": get_correlation_id() or "",
            "message_id": get_message_id() or "",
        }

    @staticmethod
    def send_form_panel_created(
        *, tenant_id: UUID, form_panel_id: UUID, form_id: UUID, payload: Dict[str, Any]
    ) -> None:
        message = FormPanelCreatedMessage(
            tenant_id=tenant_id,
            form_panel_id=form_panel_id,
            form_id=form_id,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormPanelCreatedMessage)
        celery_app.send_task(
            "conversa.form-panel.created",
            args=[envelope.model_dump(mode="json")],
            headers=FormPanelProducer._build_headers(),
        )

    @staticmethod
    def send_form_panel_updated(
        *,
        tenant_id: UUID,
        form_panel_id: UUID,
        form_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        message = FormPanelUpdatedMessage(
            tenant_id=tenant_id,
            form_panel_id=form_panel_id,
            form_id=form_id,
            changes=changes,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormPanelUpdatedMessage)
        celery_app.send_task(
            "conversa.form-panel.updated",
            args=[envelope.model_dump(mode="json")],
            headers=FormPanelProducer._build_headers(),
        )

    @staticmethod
    def send_form_panel_deleted(
        *, tenant_id: UUID, form_panel_id: UUID, form_id: UUID
    ) -> None:
        message = FormPanelDeletedMessage(
            tenant_id=tenant_id,
            form_panel_id=form_panel_id,
            form_id=form_id,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormPanelDeletedMessage)
        celery_app.send_task(
            "conversa.form-panel.deleted",
            args=[envelope.model_dump(mode="json")],
            headers=FormPanelProducer._build_headers(),
        )