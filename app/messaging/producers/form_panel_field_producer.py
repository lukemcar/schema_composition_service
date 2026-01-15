"""
Celery producer for FormPanelField events.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import celery_app
from app.domain.schemas.events import (
    FormPanelFieldCreatedMessage,
    FormPanelFieldUpdatedMessage,
    FormPanelFieldDeletedMessage,
)
from app.domain.schemas.events.common import EventEnvelope
from app.util.correlation import get_correlation_id, get_message_id


class FormPanelFieldProducer:
    """Publish FormPanelField lifecycle events."""

    @staticmethod
    def _build_headers() -> Dict[str, str]:
        return {
            "correlation_id": get_correlation_id() or "",
            "message_id": get_message_id() or "",
        }

    @staticmethod
    def send_form_panel_field_created(
        *,
        tenant_id: UUID,
        form_panel_field_id: UUID,
        form_panel_id: UUID,
        field_def_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        message = FormPanelFieldCreatedMessage(
            tenant_id=tenant_id,
            form_panel_field_id=form_panel_field_id,
            form_panel_id=form_panel_id,
            field_def_id=field_def_id,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormPanelFieldCreatedMessage)
        celery_app.send_task(
            "SchemaComposition.form-panel-field.created",
            args=[envelope.model_dump(mode="json")],
            headers=FormPanelFieldProducer._build_headers(),
        )

    @staticmethod
    def send_form_panel_field_updated(
        *,
        tenant_id: UUID,
        form_panel_field_id: UUID,
        form_panel_id: UUID,
        field_def_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        message = FormPanelFieldUpdatedMessage(
            tenant_id=tenant_id,
            form_panel_field_id=form_panel_field_id,
            form_panel_id=form_panel_id,
            field_def_id=field_def_id,
            changes=changes,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormPanelFieldUpdatedMessage)
        celery_app.send_task(
            "SchemaComposition.form-panel-field.updated",
            args=[envelope.model_dump(mode="json")],
            headers=FormPanelFieldProducer._build_headers(),
        )

    @staticmethod
    def send_form_panel_field_deleted(
        *,
        tenant_id: UUID,
        form_panel_field_id: UUID,
        form_panel_id: UUID,
        field_def_id: UUID,
    ) -> None:
        message = FormPanelFieldDeletedMessage(
            tenant_id=tenant_id,
            form_panel_field_id=form_panel_field_id,
            form_panel_id=form_panel_id,
            field_def_id=field_def_id,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormPanelFieldDeletedMessage)
        celery_app.send_task(
            "SchemaComposition.form-panel-field.deleted",
            args=[envelope.model_dump(mode="json")],
            headers=FormPanelFieldProducer._build_headers(),
        )