# app/core/celery_app.py
from __future__ import annotations

from celery import Celery
from kombu import Exchange, Queue

from app.core.config import Config
from app.core.telemetry import init_tracing, instrument_celery


# Single, shared Celery application for the whole service.
#
# The name passed here identifies this worker in monitoring tools and
# does not affect routing.  Use a descriptive name to match your
# service; when extending this template copy this line and adjust
# accordingly.
celery_app = Celery("my-entity-service")

# --------------------------------------------------------------------
# Core broker / backend config (RabbitMQ 4.2.1, JSON only, no pickle)
# --------------------------------------------------------------------
celery_app.conf.update(
    broker_url=Config.celery_broker_url(),
    result_backend=Config.celery_result_backend(),

    # Safety & interoperability
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    enable_utc=True,
    timezone="UTC",

    # Retry connecting to broker on startup (good with RabbitMQ restarts)
    broker_connection_retry_on_startup=True,
)

# --------------------------------------------------------------------
# Exchanges, queues, and routing (simplified for MyEntity)
# --------------------------------------------------------------------
# Use a single topic exchange for all events.  We define one domain queue
# for ``my-entity`` events and a corresponding dead letter queue.  When
# extending the service to additional domains, add queues and routes here
# following the same pattern.

conversa_exchange = Exchange("conversa", type="topic")
conversa_dlx = Exchange("conversa.dlx", type="topic")

celery_app.conf.task_default_exchange = conversa_exchange.name
celery_app.conf.task_default_exchange_type = conversa_exchange.type
celery_app.conf.task_default_routing_key = "conversa.default"

celery_app.conf.task_queues = (
    # Generic catch‑all queue
    Queue(
        "conversa.default",
        exchange=conversa_exchange,
        routing_key="conversa.default",
    ),
    # Domain queue for MyEntity events
    Queue(
        "conversa.my-entity",
        exchange=conversa_exchange,
        routing_key="conversa.my-entity.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "conversa.my-entity.dlq",
        },
    ),
    # Domain queue for FormCatalogCategory events
    Queue(
        "conversa.form-catalog-category",
        exchange=conversa_exchange,
        routing_key="conversa.form-catalog-category.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "conversa.form-catalog-category.dlq",
        },
    ),
    # Domain queue for FieldDef events
    Queue(
        "conversa.field-def",
        exchange=conversa_exchange,
        routing_key="conversa.field-def.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "conversa.field-def.dlq",
        },
    ),
    # Domain queue for FieldDefOption events
    Queue(
        "conversa.field-def-option",
        exchange=conversa_exchange,
        routing_key="conversa.field-def-option.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "conversa.field-def-option.dlq",
        },
    ),

    # Domain queue for Component events
    Queue(
        "conversa.component",
        exchange=conversa_exchange,
        routing_key="conversa.component.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "conversa.component.dlq",
        },
    ),
    # Domain queue for ComponentPanel events
    Queue(
        "conversa.component-panel",
        exchange=conversa_exchange,
        routing_key="conversa.component-panel.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "conversa.component-panel.dlq",
        },
    ),
    # Domain queue for ComponentPanelField events
    Queue(
        "conversa.component-panel-field",
        exchange=conversa_exchange,
        routing_key="conversa.component-panel-field.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "conversa.component-panel-field.dlq",
        },
    ),
    # Domain queue for Form events
    Queue(
        "conversa.form",
        exchange=conversa_exchange,
        routing_key="conversa.form.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "conversa.form.dlq",
        },
    ),
    # Domain queue for FormPanel events
    Queue(
        "conversa.form-panel",
        exchange=conversa_exchange,
        routing_key="conversa.form-panel.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "conversa.form-panel.dlq",
        },
    ),
    # Domain queue for FormPanelComponent events
    Queue(
        "conversa.form-panel-component",
        exchange=conversa_exchange,
        routing_key="conversa.form-panel-component.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "conversa.form-panel-component.dlq",
        },
    ),
    # Domain queue for FormPanelField events
    Queue(
        "conversa.form-panel-field",
        exchange=conversa_exchange,
        routing_key="conversa.form-panel-field.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "conversa.form-panel-field.dlq",
        },
    ),
    # Domain queue for FormSubmission events
    Queue(
        "conversa.form-submission",
        exchange=conversa_exchange,
        routing_key="conversa.form-submission.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "conversa.form-submission.dlq",
        },
    ),
    # Domain queue for FormSubmissionValue events
    Queue(
        "conversa.form-submission-value",
        exchange=conversa_exchange,
        routing_key="conversa.form-submission-value.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "conversa.form-submission-value.dlq",
        },
    ),
)

celery_app.conf.task_queues += (
    # Dead letter queue for MyEntity events
    Queue(
        "conversa.my-entity.dlq",
        exchange=conversa_dlx,
        routing_key="conversa.my-entity.dlq",
    ),
    # Dead letter queue for FormCatalogCategory events
    Queue(
        "conversa.form-catalog-category.dlq",
        exchange=conversa_dlx,
        routing_key="conversa.form-catalog-category.dlq",
    ),
    # Dead letter queue for FieldDef events
    Queue(
        "conversa.field-def.dlq",
        exchange=conversa_dlx,
        routing_key="conversa.field-def.dlq",
    ),
    # Dead letter queue for FieldDefOption events
    Queue(
        "conversa.field-def-option.dlq",
        exchange=conversa_dlx,
        routing_key="conversa.field-def-option.dlq",
    ),

    # Dead letter queue for Component events
    Queue(
        "conversa.component.dlq",
        exchange=conversa_dlx,
        routing_key="conversa.component.dlq",
    ),
    # Dead letter queue for ComponentPanel events
    Queue(
        "conversa.component-panel.dlq",
        exchange=conversa_dlx,
        routing_key="conversa.component-panel.dlq",
    ),
    # Dead letter queue for ComponentPanelField events
    Queue(
        "conversa.component-panel-field.dlq",
        exchange=conversa_dlx,
        routing_key="conversa.component-panel-field.dlq",
    ),
    # Dead letter queue for Form events
    Queue(
        "conversa.form.dlq",
        exchange=conversa_dlx,
        routing_key="conversa.form.dlq",
    ),
    # Dead letter queue for FormPanel events
    Queue(
        "conversa.form-panel.dlq",
        exchange=conversa_dlx,
        routing_key="conversa.form-panel.dlq",
    ),
    # Dead letter queue for FormPanelComponent events
    Queue(
        "conversa.form-panel-component.dlq",
        exchange=conversa_dlx,
        routing_key="conversa.form-panel-component.dlq",
    ),
    # Dead letter queue for FormPanelField events
    Queue(
        "conversa.form-panel-field.dlq",
        exchange=conversa_dlx,
        routing_key="conversa.form-panel-field.dlq",
    ),
    # Dead letter queue for FormSubmission events
    Queue(
        "conversa.form-submission.dlq",
        exchange=conversa_dlx,
        routing_key="conversa.form-submission.dlq",
    ),
    # Dead letter queue for FormSubmissionValue events
    Queue(
        "conversa.form-submission-value.dlq",
        exchange=conversa_dlx,
        routing_key="conversa.form-submission-value.dlq",
    ),
)

celery_app.conf.task_routes = {
    # Routes for MyEntity lifecycle events
    "conversa.my-entity.created": {
        "queue": "conversa.my-entity",
        "routing_key": "conversa.my-entity.created",
    },
    "conversa.my-entity.updated": {
        "queue": "conversa.my-entity",
        "routing_key": "conversa.my-entity.updated",
    },
    "conversa.my-entity.deleted": {
        "queue": "conversa.my-entity",
        "routing_key": "conversa.my-entity.deleted",
    },

    # Routes for FormCatalogCategory lifecycle events
    "conversa.form-catalog-category.created": {
        "queue": "conversa.form-catalog-category",
        "routing_key": "conversa.form-catalog-category.created",
    },
    "conversa.form-catalog-category.updated": {
        "queue": "conversa.form-catalog-category",
        "routing_key": "conversa.form-catalog-category.updated",
    },
    "conversa.form-catalog-category.deleted": {
        "queue": "conversa.form-catalog-category",
        "routing_key": "conversa.form-catalog-category.deleted",
    },

    # Routes for FieldDef lifecycle events
    "conversa.field-def.created": {
        "queue": "conversa.field-def",
        "routing_key": "conversa.field-def.created",
    },
    "conversa.field-def.updated": {
        "queue": "conversa.field-def",
        "routing_key": "conversa.field-def.updated",
    },
    "conversa.field-def.deleted": {
        "queue": "conversa.field-def",
        "routing_key": "conversa.field-def.deleted",
    },

    # Routes for FieldDefOption lifecycle events
    "conversa.field-def-option.created": {
        "queue": "conversa.field-def-option",
        "routing_key": "conversa.field-def-option.created",
    },
    "conversa.field-def-option.updated": {
        "queue": "conversa.field-def-option",
        "routing_key": "conversa.field-def-option.updated",
    },
    "conversa.field-def-option.deleted": {
        "queue": "conversa.field-def-option",
        "routing_key": "conversa.field-def-option.deleted",
    },

    # Routes for Component lifecycle events
    "conversa.component.created": {
        "queue": "conversa.component",
        "routing_key": "conversa.component.created",
    },
    "conversa.component.updated": {
        "queue": "conversa.component",
        "routing_key": "conversa.component.updated",
    },
    "conversa.component.deleted": {
        "queue": "conversa.component",
        "routing_key": "conversa.component.deleted",
    },

    # Routes for ComponentPanel lifecycle events
    "conversa.component-panel.created": {
        "queue": "conversa.component-panel",
        "routing_key": "conversa.component-panel.created",
    },
    "conversa.component-panel.updated": {
        "queue": "conversa.component-panel",
        "routing_key": "conversa.component-panel.updated",
    },
    "conversa.component-panel.deleted": {
        "queue": "conversa.component-panel",
        "routing_key": "conversa.component-panel.deleted",
    },

    # Routes for ComponentPanelField lifecycle events
    "conversa.component-panel-field.created": {
        "queue": "conversa.component-panel-field",
        "routing_key": "conversa.component-panel-field.created",
    },
    "conversa.component-panel-field.updated": {
        "queue": "conversa.component-panel-field",
        "routing_key": "conversa.component-panel-field.updated",
    },
    "conversa.component-panel-field.deleted": {
        "queue": "conversa.component-panel-field",
        "routing_key": "conversa.component-panel-field.deleted",
    },

    # Routes for Form lifecycle events
    "conversa.form.created": {
        "queue": "conversa.form",
        "routing_key": "conversa.form.created",
    },
    "conversa.form.updated": {
        "queue": "conversa.form",
        "routing_key": "conversa.form.updated",
    },
    "conversa.form.deleted": {
        "queue": "conversa.form",
        "routing_key": "conversa.form.deleted",
    },

    # Routes for FormPanel lifecycle events
    "conversa.form-panel.created": {
        "queue": "conversa.form-panel",
        "routing_key": "conversa.form-panel.created",
    },
    "conversa.form-panel.updated": {
        "queue": "conversa.form-panel",
        "routing_key": "conversa.form-panel.updated",
    },
    "conversa.form-panel.deleted": {
        "queue": "conversa.form-panel",
        "routing_key": "conversa.form-panel.deleted",
    },

    # Routes for FormPanelComponent lifecycle events
    "conversa.form-panel-component.created": {
        "queue": "conversa.form-panel-component",
        "routing_key": "conversa.form-panel-component.created",
    },
    "conversa.form-panel-component.updated": {
        "queue": "conversa.form-panel-component",
        "routing_key": "conversa.form-panel-component.updated",
    },
    "conversa.form-panel-component.deleted": {
        "queue": "conversa.form-panel-component",
        "routing_key": "conversa.form-panel-component.deleted",
    },

    # Routes for FormPanelField lifecycle events
    "conversa.form-panel-field.created": {
        "queue": "conversa.form-panel-field",
        "routing_key": "conversa.form-panel-field.created",
    },
    "conversa.form-panel-field.updated": {
        "queue": "conversa.form-panel-field",
        "routing_key": "conversa.form-panel-field.updated",
    },
    "conversa.form-panel-field.deleted": {
        "queue": "conversa.form-panel-field",
        "routing_key": "conversa.form-panel-field.deleted",
    },

    # Routes for FormSubmission lifecycle events
    "conversa.form-submission.created": {
        "queue": "conversa.form-submission",
        "routing_key": "conversa.form-submission.created",
    },
    "conversa.form-submission.updated": {
        "queue": "conversa.form-submission",
        "routing_key": "conversa.form-submission.updated",
    },
    "conversa.form-submission.deleted": {
        "queue": "conversa.form-submission",
        "routing_key": "conversa.form-submission.deleted",
    },

    # Routes for FormSubmissionValue lifecycle events
    "conversa.form-submission-value.created": {
        "queue": "conversa.form-submission-value",
        "routing_key": "conversa.form-submission-value.created",
    },
    "conversa.form-submission-value.updated": {
        "queue": "conversa.form-submission-value",
        "routing_key": "conversa.form-submission-value.updated",
    },
    "conversa.form-submission-value.deleted": {
        "queue": "conversa.form-submission-value",
        "routing_key": "conversa.form-submission-value.deleted",
    },
}

# --------------------------------------------------------------------
# Task discovery (for the *consumer* side)
# --------------------------------------------------------------------
celery_app.autodiscover_tasks(
    [
        "app.messaging",
    ]
)

# Initialise telemetry for Celery workers when they start up.  We
# configure a distinct service name for the worker so traces can be
# distinguished from API spans in observability tools.  If
# instrumentation libraries are unavailable this silently does
# nothing.
try:
    init_tracing(service_name="my-entity-worker")
    instrument_celery(celery_app)
    # Instrument httpx globally for Celery worker processes.
    from app.core.telemetry import instrument_httpx
    instrument_httpx()
except Exception:
    # Telemetry may not be available; ignore.
    pass
