"""
Celery producer for Form events.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import celery_app
from app.domain.schemas.events import (
    FormCreatedMessage,
    FormUpdatedMessage,
    FormDeletedMessage,
)
from app.domain.schemas.events.common import EventEnvelope
from app.util.correlation import get_correlation_id, get_message_id


class FormProducer:
    """Publish Form lifecycle events via Celery."""

    @staticmethod
    def _build_headers() -> Dict[str, str]:
        return {
            "correlation_id": get_correlation_id() or "",
            "message_id": get_message_id() or "",
        }

    @staticmethod
    def send_form_created(*, tenant_id: UUID, form_id: UUID, payload: Dict[str, Any]) -> None:
        message = FormCreatedMessage(
            tenant_id=tenant_id,
            form_id=form_id,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormCreatedMessage)
        celery_app.send_task(
            "conversa.form.created",
            args=[envelope.model_dump(mode="json")],
            headers=FormProducer._build_headers(),
        )

    @staticmethod
    def send_form_updated(
        *, tenant_id: UUID, form_id: UUID, changes: Dict[str, Any], payload: Dict[str, Any]
    ) -> None:
        message = FormUpdatedMessage(
            tenant_id=tenant_id,
            form_id=form_id,
            changes=changes,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormUpdatedMessage)
        celery_app.send_task(
            "conversa.form.updated",
            args=[envelope.model_dump(mode="json")],
            headers=FormProducer._build_headers(),
        )

    @staticmethod
    def send_form_deleted(*, tenant_id: UUID, form_id: UUID) -> None:
        message = FormDeletedMessage(
            tenant_id=tenant_id,
            form_id=form_id,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormDeletedMessage)
        celery_app.send_task(
            "conversa.form.deleted",
            args=[envelope.model_dump(mode="json")],
            headers=FormProducer._build_headers(),
        )