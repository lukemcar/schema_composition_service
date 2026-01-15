"""
Celery producer for FormSubmission events.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from app.core.celery_app import celery_app
from app.domain.schemas.events import (
    FormSubmissionCreatedMessage,
    FormSubmissionUpdatedMessage,
    FormSubmissionDeletedMessage,
)
from app.domain.schemas.events.common import EventEnvelope
from app.util.correlation import get_correlation_id, get_message_id


class FormSubmissionProducer:
    """Publish FormSubmission lifecycle events via Celery."""

    @staticmethod
    def _build_headers() -> Dict[str, str]:
        return {
            "correlation_id": get_correlation_id() or "",
            "message_id": get_message_id() or "",
        }

    @staticmethod
    def send_form_submission_created(
        *, tenant_id: UUID, form_submission_id: UUID, form_id: UUID, payload: Dict[str, Any]
    ) -> None:
        message = FormSubmissionCreatedMessage(
            tenant_id=tenant_id,
            form_submission_id=form_submission_id,
            form_id=form_id,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormSubmissionCreatedMessage)
        celery_app.send_task(
            "SchemaComposition.form-submission.created",
            args=[envelope.model_dump(mode="json")],
            headers=FormSubmissionProducer._build_headers(),
        )

    @staticmethod
    def send_form_submission_updated(
        *,
        tenant_id: UUID,
        form_submission_id: UUID,
        form_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        message = FormSubmissionUpdatedMessage(
            tenant_id=tenant_id,
            form_submission_id=form_submission_id,
            form_id=form_id,
            changes=changes,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormSubmissionUpdatedMessage)
        celery_app.send_task(
            "SchemaComposition.form-submission.updated",
            args=[envelope.model_dump(mode="json")],
            headers=FormSubmissionProducer._build_headers(),
        )

    @staticmethod
    def send_form_submission_deleted(
        *, tenant_id: UUID, form_submission_id: UUID, form_id: UUID
    ) -> None:
        message = FormSubmissionDeletedMessage(
            tenant_id=tenant_id,
            form_submission_id=form_submission_id,
            form_id=form_id,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FormSubmissionDeletedMessage)
        celery_app.send_task(
            "SchemaComposition.form-submission.deleted",
            args=[envelope.model_dump(mode="json")],
            headers=FormSubmissionProducer._build_headers(),
        )