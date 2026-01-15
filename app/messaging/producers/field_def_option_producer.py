"""
Celery producer for FieldDefOption events.

This module defines helper functions for publishing created, updated and
deleted events for FieldDefOption resources.  Messages are sent via
RabbitMQ using Celery and follow the standard event naming convention.
"""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID

from celery import Celery

from app.core.celery_app import celery_app
from app.domain.schemas.events import (
    FieldDefOptionCreatedMessage,
    FieldDefOptionUpdatedMessage,
    FieldDefOptionDeletedMessage,
)
from app.domain.schemas.events.common import EventEnvelope
from app.util.correlation import get_correlation_id, get_message_id


class FieldDefOptionProducer:
    """Publish FieldDefOption lifecycle events via Celery."""

    @staticmethod
    def _build_headers() -> Dict[str, str]:
        """Return common headers for all events including correlation IDs."""
        return {
            "correlation_id": get_correlation_id() or "",  # attach if available
            "message_id": get_message_id() or "",
        }

    @staticmethod
    def send_field_def_option_created(
        *, tenant_id: UUID, field_def_option_id: UUID, field_def_id: UUID, payload: Dict[str, Any]
    ) -> None:
        """Publish a field-def-option.created event."""
        message = FieldDefOptionCreatedMessage(
            tenant_id=tenant_id,
            field_def_option_id=field_def_option_id,
            field_def_id=field_def_id,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FieldDefOptionCreatedMessage)
        celery_app.send_task(
            "SchemaComposition.field-def-option.created",
            args=[envelope.model_dump(mode="json")],
            headers=FieldDefOptionProducer._build_headers(),
        )

    @staticmethod
    def send_field_def_option_updated(
        *, tenant_id: UUID, field_def_option_id: UUID, field_def_id: UUID, changes: Dict[str, Any], payload: Dict[str, Any]
    ) -> None:
        """Publish a field-def-option.updated event."""
        message = FieldDefOptionUpdatedMessage(
            tenant_id=tenant_id,
            field_def_option_id=field_def_option_id,
            field_def_id=field_def_id,
            changes=changes,
            payload=payload,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FieldDefOptionUpdatedMessage)
        celery_app.send_task(
            "SchemaComposition.field-def-option.updated",
            args=[envelope.model_dump(mode="json")],
            headers=FieldDefOptionProducer._build_headers(),
        )

    @staticmethod
    def send_field_def_option_deleted(
        *, tenant_id: UUID, field_def_option_id: UUID, field_def_id: UUID
    ) -> None:
        """Publish a field-def-option.deleted event."""
        message = FieldDefOptionDeletedMessage(
            tenant_id=tenant_id,
            field_def_option_id=field_def_option_id,
            field_def_id=field_def_id,
        )
        envelope = EventEnvelope.create(message.model_dump(mode="json"), FieldDefOptionDeletedMessage)
        celery_app.send_task(
            "SchemaComposition.field-def-option.deleted",
            args=[envelope.model_dump(mode="json")],
            headers=FieldDefOptionProducer._build_headers(),
        )