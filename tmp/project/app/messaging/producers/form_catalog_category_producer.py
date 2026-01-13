"""
Producer for FormCatalogCategory domain events.

This module defines a producer class for publishing
FormCatalogCategory lifecycle events via Celery/RabbitMQ.  Each
method wraps the corresponding domain payload in an ``EventEnvelope``
and sends it through the shared Celery application.  When adding
another domain, copy this producer and adjust the task names,
headers and payload models accordingly.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4

from app.core.celery_app import celery_app
from app.domain.schemas.events.form_catalog_category_events import (
    FormCatalogCategoryCreatedMessage,
    FormCatalogCategoryUpdatedMessage,
    FormCatalogCategoryDeletedMessage,
)
from app.domain.schemas.events.common import EventEnvelope
from app.util.correlation import (
    get_correlation_id,
    get_message_id,
    set_message_id,
)


class FormCatalogCategoryProducer:
    """Publishes FormCatalogCategory events via Celery.

    The task names double as routing keys on the ``conversa`` exchange.
    They follow the naming convention ``conversa.<domain>.<event>`` to
    enable fine‑grained routing by queue bindings.  When creating a new
    producer for your domain follow this pattern and ensure the Celery
    configuration defines matching routes.
    """

    TASK_CREATED = "conversa.form-catalog-category.created"
    TASK_UPDATED = "conversa.form-catalog-category.updated"
    TASK_DELETED = "conversa.form-catalog-category.deleted"

    @staticmethod
    def _build_headers(*, tenant_id: UUID, form_catalog_category_id: UUID) -> Dict[str, str]:
        """Construct message headers with identifiers for traceability.

        Headers are optional metadata that accompany the message and
        allow consumers to quickly access key identifiers without
        inspecting the payload.  Include tenant and category IDs here.
        """
        return {
            "tenant_id": str(tenant_id),
            "form_catalog_category_id": str(form_catalog_category_id),
        }

    @classmethod
    def _send(
        cls,
        *,
        task_name: str,
        message_model: Any,
        headers: Dict[str, str],
    ) -> None:
        """Internal helper: wrap the domain message in an EventEnvelope and send it.

        The envelope captures metadata such as event identifiers,
        correlation/causation IDs and timestamps.  The Celery task name is
        used both as the ``event_type`` and the routing key.
        """
        payload = message_model.model_dump(mode="json")
        envelope = EventEnvelope(
            event_id=uuid4(),
            event_type=task_name,
            schema_version=1,
            occurred_at=datetime.utcnow(),
            producer="my-entity-service",
            tenant_id=message_model.tenant_id,
            correlation_id=get_correlation_id(),
            causation_id=get_message_id(),
            traceparent=None,
            data=payload,
        )
        # Set the new event_id as the causation ID for downstream events
        set_message_id(str(envelope.event_id))
        correlation_headers = {
            "message_id": str(envelope.event_id),
            "correlation_id": str(envelope.correlation_id)
            if envelope.correlation_id is not None
            else None,
            "causation_id": str(envelope.causation_id)
            if envelope.causation_id is not None
            else None,
        }
        correlation_headers = {k: v for k, v in correlation_headers.items() if v}
        combined_headers = {**headers, **correlation_headers}
        celery_app.send_task(
            name=task_name,
            kwargs={"envelope": envelope.model_dump(mode="json")},
            headers=combined_headers,
        )

    @classmethod
    def send_form_catalog_category_created(
        cls,
        *,
        tenant_id: UUID,
        form_catalog_category_id: UUID,
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ``form-catalog-category.created`` event.

        Args:
            tenant_id: The tenant that owns the category.
            form_catalog_category_id: The primary key of the created category.
            payload: The full category state to include in the event body.
        """
        message = FormCatalogCategoryCreatedMessage(
            tenant_id=tenant_id,
            form_catalog_category_id=form_catalog_category_id,
            payload=payload,
        )
        headers = cls._build_headers(
            tenant_id=tenant_id,
            form_catalog_category_id=form_catalog_category_id,
        )
        cls._send(task_name=cls.TASK_CREATED, message_model=message, headers=headers)

    @classmethod
    def send_form_catalog_category_updated(
        cls,
        *,
        tenant_id: UUID,
        form_catalog_category_id: UUID,
        changes: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> None:
        """Publish a ``form-catalog-category.updated`` event.

        Args:
            tenant_id: Tenant owning the category.
            form_catalog_category_id: Identifier of the updated category.
            changes: A dictionary of fields that were modified.
            payload: The full updated category state.
        """
        message = FormCatalogCategoryUpdatedMessage(
            tenant_id=tenant_id,
            form_catalog_category_id=form_catalog_category_id,
            changes=changes,
            payload=payload,
        )
        headers = cls._build_headers(
            tenant_id=tenant_id,
            form_catalog_category_id=form_catalog_category_id,
        )
        cls._send(task_name=cls.TASK_UPDATED, message_model=message, headers=headers)

    @classmethod
    def send_form_catalog_category_deleted(
        cls,
        *,
        tenant_id: UUID,
        form_catalog_category_id: UUID,
        deleted_dt: str | None = None,
    ) -> None:
        """Publish a ``form-catalog-category.deleted`` event.

        Args:
            tenant_id: Tenant owning the category.
            form_catalog_category_id: Identifier of the deleted category.
            deleted_dt: Optional ISO‑formatted deletion timestamp.  If
                not provided the consumer may use its own timestamp.
        """
        message = FormCatalogCategoryDeletedMessage(
            tenant_id=tenant_id,
            form_catalog_category_id=form_catalog_category_id,
            deleted_dt=deleted_dt,
        )
        headers = cls._build_headers(
            tenant_id=tenant_id,
            form_catalog_category_id=form_catalog_category_id,
        )
        cls._send(task_name=cls.TASK_DELETED, message_model=message, headers=headers)


__all__ = ["FormCatalogCategoryProducer"]