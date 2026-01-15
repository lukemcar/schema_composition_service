# Analysis – Messaging Layer

The messaging layer is responsible for publishing domain events to
RabbitMQ via Celery and processing incoming events.  It consists of
producers (publishers) and tasks (consumers).

## Producers

Every domain defined in the simplified DDL has a dedicated producer
module responsible for publishing lifecycle events to the message bus.
A producer exposes static methods to emit ``created``, ``updated`` and
``deleted`` events.  Each method constructs an `EventEnvelope` from a
Pydantic message class, injects correlation and message identifiers
using the correlation utilities and sends the envelope via Celery.  The
routing keys follow a consistent convention: ``SchemaComposition.<domain>.<event>``.

After the initial implementation for `FormCatalogCategory` and
`FieldDef`, producers were added for every remaining domain object.  The
full list of producer modules now includes:

* `FieldDefOptionProducer`
* `ComponentProducer`
* `ComponentPanelProducer`
* `ComponentPanelFieldProducer`
* `FormProducer`
* `FormPanelProducer`
* `FormPanelComponentProducer`
* `FormPanelFieldProducer`
* `FormSubmissionProducer`
* `FormSubmissionValueProducer`

This uniform producer pattern guarantees that events across all
domains carry the same metadata and structure, simplifying consumption
by downstream services.

## Tasks

For each producer there is a corresponding set of Celery tasks defined
under `app/messaging/tasks`.  Tasks listen on domain‑specific queues
and handle incoming messages by parsing the event envelope, propagating
correlation and trace context and logging the event payload.  Handlers
exist for the `created`, `updated` and `deleted` events for every
domain: `field_def_option`, `component`, `component_panel`,
`component_panel_field`, `form`, `form_panel`, `form_panel_component`,
`form_panel_field`, `form_submission` and `form_submission_value` in
addition to the previously implemented handlers for
`form_catalog_category` and `field_def`.

Tasks rely on `eventutils.propagate_context` to ensure that tracing
context propagates across asynchronous boundaries.  They are currently
placeholders that log incoming messages but can be extended with
domain‑specific side effects, such as updating caches or triggering
downstream workflows.

## Celery Configuration

The Celery application (`app/core/celery_app.py`) was expanded to
declare queues for every domain.  For each domain ``x`` a durable
queue ``SchemaComposition.x`` and a dead‑letter queue ``SchemaComposition.x.dlq`` are
created.  Routing rules map the task names ``SchemaComposition.x.created``,
``SchemaComposition.x.updated`` and ``SchemaComposition.x.deleted`` to the appropriate
queue.  The application continues to automatically discover tasks in
`app/messaging/tasks` and applies OpenTelemetry instrumentation to
instrument Celery and HTTPX interactions.  No changes were made to
broker configuration or retry policies.

With all domain queues and routing keys in place, the messaging layer is
now fully prepared to publish and consume events for every table in the
simplified DDL.