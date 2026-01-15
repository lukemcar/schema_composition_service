"""
Celery producer for FormSubmissionValue events.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import celery_app
from app.domain.schemas.events import (
    FormSubmissionValueCreatedMessage,
    FormSubmissionValueUpdatedMessage,
    FormSubmissionValueDeletedMessage,
)
from app.domain.schemas.events.common import EventEnvelope
from app.util.correlation import get_correlation_id, get_message_id


class FormSubmissionValueProducer:
    """Publish FormSubmissionValue lifecycle events via Celery."""

    @staticmethod
    def _build_headers() -> Dict[str, str]:
        return {
            "correlation_id": get_correlation_id() or "",
            "message_id": get_message_id() or "",
        }

    @staticmethod
    def send_form_submission_value_created(
        *,
        tenant_id: UUID,
        form_submission_value_id: UUID,
        form_submission_id: UUID,
        field_instance_path: str,
        payload: Dict[str, Any],
    ) -> None:
        message = FormSubmissionValueCreatedMessage(
            tenant_id=tenant_id,
            form_submission_value_id=form_submission_value_id,
            form_submission_id=form_submission_id,
            field_instance_path=field_instance_path,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormSubmissionValueCreatedMessage)
        celery_app.send_task(
            "SchemaComposition.form-submission-value.created",
            args=[envelope.model_dump(mode="json")],
            headers=FormSubmissionValueProducer._build_headers(),
        )

    @staticmethod
    def send_form_submission_value_updated(
        *,
        tenant_id: UUID,
        form_submission_value_id: UUID,
        form_submission_id: UUID,
        field_instance_path: str,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        message = FormSubmissionValueUpdatedMessage(
            tenant_id=tenant_id,
            form_submission_value_id=form_submission_value_id,
            form_submission_id=form_submission_id,
            field_instance_path=field_instance_path,
            changes=changes,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormSubmissionValueUpdatedMessage)
        celery_app.send_task(
            "SchemaComposition.form-submission-value.updated",
            args=[envelope.model_dump(mode="json")],
            headers=FormSubmissionValueProducer._build_headers(),
        )

    @staticmethod
    def send_form_submission_value_deleted(
        *,
        tenant_id: UUID,
        form_submission_value_id: UUID,
        form_submission_id: UUID,
        field_instance_path: str,
    ) -> None:
        message = FormSubmissionValueDeletedMessage(
            tenant_id=tenant_id,
            form_submission_value_id=form_submission_value_id,
            form_submission_id=form_submission_id,
            field_instance_path=field_instance_path,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormSubmissionValueDeletedMessage)
        celery_app.send_task(
            "SchemaComposition.form-submission-value.deleted",
            args=[envelope.model_dump(mode="json")],
            headers=FormSubmissionValueProducer._build_headers(),
        )