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
celery_app = Celery("schema-composition-service")

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
# Exchanges, queues, and routing (simplified for SchemaComposition)
# --------------------------------------------------------------------
# Use a single topic exchange for all events.  We define one domain queue
# for ``schema-composition`` events and a corresponding dead letter queue.  When
# extending the service to additional domains, add queues and routes here
# following the same pattern.

conversa_exchange = Exchange("SchemaComposition", type="topic")
conversa_dlx = Exchange("SchemaComposition.dlx", type="topic")

celery_app.conf.task_default_exchange = conversa_exchange.name
celery_app.conf.task_default_exchange_type = conversa_exchange.type
celery_app.conf.task_default_routing_key = "SchemaComposition.default"

celery_app.conf.task_queues = (
    # Generic catch‑all queue
    Queue(
        "SchemaComposition.default",
        exchange=conversa_exchange,
        routing_key="SchemaComposition.default",
    ),
    # Domain queue for SchemaComposition events
    Queue(
        "SchemaComposition.schema-composition",
        exchange=conversa_exchange,
        routing_key="SchemaComposition.schema-composition.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "SchemaComposition.schema-composition.dlq",
        },
    ),
    # Domain queue for FormCatalogCategory events
    Queue(
        "SchemaComposition.form-catalog-category",
        exchange=conversa_exchange,
        routing_key="SchemaComposition.form-catalog-category.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "SchemaComposition.form-catalog-category.dlq",
        },
    ),
    # Domain queue for FieldDef events
    Queue(
        "SchemaComposition.field-def",
        exchange=conversa_exchange,
        routing_key="SchemaComposition.field-def.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "SchemaComposition.field-def.dlq",
        },
    ),
    # Domain queue for FieldDefOption events
    Queue(
        "SchemaComposition.field-def-option",
        exchange=conversa_exchange,
        routing_key="SchemaComposition.field-def-option.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "SchemaComposition.field-def-option.dlq",
        },
    ),

    # Domain queue for Component events
    Queue(
        "SchemaComposition.component",
        exchange=conversa_exchange,
        routing_key="SchemaComposition.component.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "SchemaComposition.component.dlq",
        },
    ),
    # Domain queue for ComponentPanel events
    Queue(
        "SchemaComposition.component-panel",
        exchange=conversa_exchange,
        routing_key="SchemaComposition.component-panel.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "SchemaComposition.component-panel.dlq",
        },
    ),
    # Domain queue for ComponentPanelField events
    Queue(
        "SchemaComposition.component-panel-field",
        exchange=conversa_exchange,
        routing_key="SchemaComposition.component-panel-field.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "SchemaComposition.component-panel-field.dlq",
        },
    ),
    # Domain queue for Form events
    Queue(
        "SchemaComposition.form",
        exchange=conversa_exchange,
        routing_key="SchemaComposition.form.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "SchemaComposition.form.dlq",
        },
    ),
    # Domain queue for FormPanel events
    Queue(
        "SchemaComposition.form-panel",
        exchange=conversa_exchange,
        routing_key="SchemaComposition.form-panel.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "SchemaComposition.form-panel.dlq",
        },
    ),
    # Domain queue for FormPanelComponent events
    Queue(
        "SchemaComposition.form-panel-component",
        exchange=conversa_exchange,
        routing_key="SchemaComposition.form-panel-component.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "SchemaComposition.form-panel-component.dlq",
        },
    ),
    # Domain queue for FormPanelField events
    Queue(
        "SchemaComposition.form-panel-field",
        exchange=conversa_exchange,
        routing_key="SchemaComposition.form-panel-field.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "SchemaComposition.form-panel-field.dlq",
        },
    ),
    # Domain queue for FormSubmission events
    Queue(
        "SchemaComposition.form-submission",
        exchange=conversa_exchange,
        routing_key="SchemaComposition.form-submission.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "SchemaComposition.form-submission.dlq",
        },
    ),
    # Domain queue for FormSubmissionValue events
    Queue(
        "SchemaComposition.form-submission-value",
        exchange=conversa_exchange,
        routing_key="SchemaComposition.form-submission-value.#",
        queue_arguments={
            "x-dead-letter-exchange": conversa_dlx.name,
            "x-dead-letter-routing-key": "SchemaComposition.form-submission-value.dlq",
        },
    ),
)

celery_app.conf.task_queues += (
    # Dead letter queue for SchemaComposition events
    Queue(
        "SchemaComposition.schema-composition.dlq",
        exchange=conversa_dlx,
        routing_key="SchemaComposition.schema-composition.dlq",
    ),
    # Dead letter queue for FormCatalogCategory events
    Queue(
        "SchemaComposition.form-catalog-category.dlq",
        exchange=conversa_dlx,
        routing_key="SchemaComposition.form-catalog-category.dlq",
    ),
    # Dead letter queue for FieldDef events
    Queue(
        "SchemaComposition.field-def.dlq",
        exchange=conversa_dlx,
        routing_key="SchemaComposition.field-def.dlq",
    ),
    # Dead letter queue for FieldDefOption events
    Queue(
        "SchemaComposition.field-def-option.dlq",
        exchange=conversa_dlx,
        routing_key="SchemaComposition.field-def-option.dlq",
    ),

    # Dead letter queue for Component events
    Queue(
        "SchemaComposition.component.dlq",
        exchange=conversa_dlx,
        routing_key="SchemaComposition.component.dlq",
    ),
    # Dead letter queue for ComponentPanel events
    Queue(
        "SchemaComposition.component-panel.dlq",
        exchange=conversa_dlx,
        routing_key="SchemaComposition.component-panel.dlq",
    ),
    # Dead letter queue for ComponentPanelField events
    Queue(
        "SchemaComposition.component-panel-field.dlq",
        exchange=conversa_dlx,
        routing_key="SchemaComposition.component-panel-field.dlq",
    ),
    # Dead letter queue for Form events
    Queue(
        "SchemaComposition.form.dlq",
        exchange=conversa_dlx,
        routing_key="SchemaComposition.form.dlq",
    ),
    # Dead letter queue for FormPanel events
    Queue(
        "SchemaComposition.form-panel.dlq",
        exchange=conversa_dlx,
        routing_key="SchemaComposition.form-panel.dlq",
    ),
    # Dead letter queue for FormPanelComponent events
    Queue(
        "SchemaComposition.form-panel-component.dlq",
        exchange=conversa_dlx,
        routing_key="SchemaComposition.form-panel-component.dlq",
    ),
    # Dead letter queue for FormPanelField events
    Queue(
        "SchemaComposition.form-panel-field.dlq",
        exchange=conversa_dlx,
        routing_key="SchemaComposition.form-panel-field.dlq",
    ),
    # Dead letter queue for FormSubmission events
    Queue(
        "SchemaComposition.form-submission.dlq",
        exchange=conversa_dlx,
        routing_key="SchemaComposition.form-submission.dlq",
    ),
    # Dead letter queue for FormSubmissionValue events
    Queue(
        "SchemaComposition.form-submission-value.dlq",
        exchange=conversa_dlx,
        routing_key="SchemaComposition.form-submission-value.dlq",
    ),
)

celery_app.conf.task_routes = {
    # Routes for SchemaComposition lifecycle events
    "SchemaComposition.schema-composition.created": {
        "queue": "SchemaComposition.schema-composition",
        "routing_key": "SchemaComposition.schema-composition.created",
    },
    "SchemaComposition.schema-composition.updated": {
        "queue": "SchemaComposition.schema-composition",
        "routing_key": "SchemaComposition.schema-composition.updated",
    },
    "SchemaComposition.schema-composition.deleted": {
        "queue": "SchemaComposition.schema-composition",
        "routing_key": "SchemaComposition.schema-composition.deleted",
    },

    # Routes for FormCatalogCategory lifecycle events
    "SchemaComposition.form-catalog-category.created": {
        "queue": "SchemaComposition.form-catalog-category",
        "routing_key": "SchemaComposition.form-catalog-category.created",
    },
    "SchemaComposition.form-catalog-category.updated": {
        "queue": "SchemaComposition.form-catalog-category",
        "routing_key": "SchemaComposition.form-catalog-category.updated",
    },
    "SchemaComposition.form-catalog-category.deleted": {
        "queue": "SchemaComposition.form-catalog-category",
        "routing_key": "SchemaComposition.form-catalog-category.deleted",
    },

    # Routes for FieldDef lifecycle events
    "SchemaComposition.field-def.created": {
        "queue": "SchemaComposition.field-def",
        "routing_key": "SchemaComposition.field-def.created",
    },
    "SchemaComposition.field-def.updated": {
        "queue": "SchemaComposition.field-def",
        "routing_key": "SchemaComposition.field-def.updated",
    },
    "SchemaComposition.field-def.deleted": {
        "queue": "SchemaComposition.field-def",
        "routing_key": "SchemaComposition.field-def.deleted",
    },

    # Routes for FieldDefOption lifecycle events
    "SchemaComposition.field-def-option.created": {
        "queue": "SchemaComposition.field-def-option",
        "routing_key": "SchemaComposition.field-def-option.created",
    },
    "SchemaComposition.field-def-option.updated": {
        "queue": "SchemaComposition.field-def-option",
        "routing_key": "SchemaComposition.field-def-option.updated",
    },
    "SchemaComposition.field-def-option.deleted": {
        "queue": "SchemaComposition.field-def-option",
        "routing_key": "SchemaComposition.field-def-option.deleted",
    },

    # Routes for Component lifecycle events
    "SchemaComposition.component.created": {
        "queue": "SchemaComposition.component",
        "routing_key": "SchemaComposition.component.created",
    },
    "SchemaComposition.component.updated": {
        "queue": "SchemaComposition.component",
        "routing_key": "SchemaComposition.component.updated",
    },
    "SchemaComposition.component.deleted": {
        "queue": "SchemaComposition.component",
        "routing_key": "SchemaComposition.component.deleted",
    },

    # Routes for ComponentPanel lifecycle events
    "SchemaComposition.component-panel.created": {
        "queue": "SchemaComposition.component-panel",
        "routing_key": "SchemaComposition.component-panel.created",
    },
    "SchemaComposition.component-panel.updated": {
        "queue": "SchemaComposition.component-panel",
        "routing_key": "SchemaComposition.component-panel.updated",
    },
    "SchemaComposition.component-panel.deleted": {
        "queue": "SchemaComposition.component-panel",
        "routing_key": "SchemaComposition.component-panel.deleted",
    },

    # Routes for ComponentPanelField lifecycle events
    "SchemaComposition.component-panel-field.created": {
        "queue": "SchemaComposition.component-panel-field",
        "routing_key": "SchemaComposition.component-panel-field.created",
    },
    "SchemaComposition.component-panel-field.updated": {
        "queue": "SchemaComposition.component-panel-field",
        "routing_key": "SchemaComposition.component-panel-field.updated",
    },
    "SchemaComposition.component-panel-field.deleted": {
        "queue": "SchemaComposition.component-panel-field",
        "routing_key": "SchemaComposition.component-panel-field.deleted",
    },

    # Routes for Form lifecycle events
    "SchemaComposition.form.created": {
        "queue": "SchemaComposition.form",
        "routing_key": "SchemaComposition.form.created",
    },
    "SchemaComposition.form.updated": {
        "queue": "SchemaComposition.form",
        "routing_key": "SchemaComposition.form.updated",
    },
    "SchemaComposition.form.deleted": {
        "queue": "SchemaComposition.form",
        "routing_key": "SchemaComposition.form.deleted",
    },

    # Routes for FormPanel lifecycle events
    "SchemaComposition.form-panel.created": {
        "queue": "SchemaComposition.form-panel",
        "routing_key": "SchemaComposition.form-panel.created",
    },
    "SchemaComposition.form-panel.updated": {
        "queue": "SchemaComposition.form-panel",
        "routing_key": "SchemaComposition.form-panel.updated",
    },
    "SchemaComposition.form-panel.deleted": {
        "queue": "SchemaComposition.form-panel",
        "routing_key": "SchemaComposition.form-panel.deleted",
    },

    # Routes for FormPanelComponent lifecycle events
    "SchemaComposition.form-panel-component.created": {
        "queue": "SchemaComposition.form-panel-component",
        "routing_key": "SchemaComposition.form-panel-component.created",
    },
    "SchemaComposition.form-panel-component.updated": {
        "queue": "SchemaComposition.form-panel-component",
        "routing_key": "SchemaComposition.form-panel-component.updated",
    },
    "SchemaComposition.form-panel-component.deleted": {
        "queue": "SchemaComposition.form-panel-component",
        "routing_key": "SchemaComposition.form-panel-component.deleted",
    },

    # Routes for FormPanelField lifecycle events
    "SchemaComposition.form-panel-field.created": {
        "queue": "SchemaComposition.form-panel-field",
        "routing_key": "SchemaComposition.form-panel-field.created",
    },
    "SchemaComposition.form-panel-field.updated": {
        "queue": "SchemaComposition.form-panel-field",
        "routing_key": "SchemaComposition.form-panel-field.updated",
    },
    "SchemaComposition.form-panel-field.deleted": {
        "queue": "SchemaComposition.form-panel-field",
        "routing_key": "SchemaComposition.form-panel-field.deleted",
    },

    # Routes for FormSubmission lifecycle events
    "SchemaComposition.form-submission.created": {
        "queue": "SchemaComposition.form-submission",
        "routing_key": "SchemaComposition.form-submission.created",
    },
    "SchemaComposition.form-submission.updated": {
        "queue": "SchemaComposition.form-submission",
        "routing_key": "SchemaComposition.form-submission.updated",
    },
    "SchemaComposition.form-submission.deleted": {
        "queue": "SchemaComposition.form-submission",
        "routing_key": "SchemaComposition.form-submission.deleted",
    },

    # Routes for FormSubmissionValue lifecycle events
    "SchemaComposition.form-submission-value.created": {
        "queue": "SchemaComposition.form-submission-value",
        "routing_key": "SchemaComposition.form-submission-value.created",
    },
    "SchemaComposition.form-submission-value.updated": {
        "queue": "SchemaComposition.form-submission-value",
        "routing_key": "SchemaComposition.form-submission-value.updated",
    },
    "SchemaComposition.form-submission-value.deleted": {
        "queue": "SchemaComposition.form-submission-value",
        "routing_key": "SchemaComposition.form-submission-value.deleted",
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
    init_tracing(service_name="schema-composition-worker")
    instrument_celery(celery_app)
    # Instrument httpx globally for Celery worker processes.
    from app.core.telemetry import instrument_httpx
    instrument_httpx()
except Exception:
    # Telemetry may not be available; ignore.
    pass
