# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

* **Domain enumeration support** – Added enumerations for
  ``field_data_type``, ``field_element_type`` and ``artifact_source_type``
  in a central module to prevent duplication across models and schemas.

* **Full domain implementation** – Implemented models, schemas, services,
  API routes, messaging producers/tasks and database migrations for every
  table defined in the simplified DDL.  In addition to the previously
  introduced ``FormCatalogCategory`` and ``FieldDef`` domains, this
  iteration added:
  * **FieldDefOption** – Stores selectable option values for single‑ and
    multi‑select field definitions.  Includes CRUD services, routes,
    producer/tasks and migration ``004_create_field_def_option.sql``.
  * **Component** – Defines reusable UI components.  Includes schemas,
    services, routes and migration ``005_create_component.sql``.
  * **ComponentPanel** – Organises panels within a component.  Added
    CRUD support and migration ``006_create_component_panel.sql``.
  * **ComponentPanelField** – Places a field definition onto a
    component panel.  Added services, routes and migration
    ``007_create_component_panel_field.sql``.
  * **Form** – Represents top‑level form definitions with business keys,
    metadata and lifecycle flags.  Added support and migration
    ``008_create_form.sql``.
  * **FormPanel** – Groups form elements into panels with optional
    nesting.  Added support and migration ``009_create_form_panel.sql``.
  * **FormPanelComponent** – Embeds a reusable component into a form
    panel.  Added support and migration ``010_create_form_panel_component.sql``.
  * **FormPanelField** – Places a field definition directly onto a form
    panel.  Added support and migration ``011_create_form_panel_field.sql``.
  * **FormSubmission** – Captures submission envelopes for forms,
    including status and deletion flags.  Added support and migration
    ``012_create_form_submission.sql``.
  * **FormSubmissionValue** – Stores individual field values within a
    submission, identified by a fully qualified path.  Added support
    and migration ``013_create_form_submission_value.sql``.

  For each of these domains the following layers were implemented:
  * SQLAlchemy models with tenant‑scoped primary keys, business keys,
    flags and audit columns.
  * Pydantic schemas for create, update, output and list responses.
  * Service modules implementing CRUD operations and publishing
    created/updated/deleted events via dedicated producers.
  * FastAPI route modules registered under
    ``/tenants/{tenant_id}/<resource>`` exposing standard CRUD
    endpoints with pagination and audit metadata injection.
  * Messaging producers and Celery tasks for each domain using routing
    keys of the form ``conversa.<domain>.<event>``.
  * API test modules under ``tests/api`` verifying that each route
    delegates correctly to the service layer and wraps responses.

* **Liquibase migrations** – Added sequential migrations
  (``004_create_field_def_option.sql`` through
  ``013_create_form_submission_value.sql``) to create all remaining
  tables with appropriate constraints and indexes.  These files are
  picked up automatically by ``changelog-root.xml``.

### Changed

* Updated ``main_api.py`` to register routers for all new domains, so
  endpoints for options, components, panels, fields, forms and
  submissions are available under their tenant‑scoped prefixes.
* Updated ``app/core/db.py`` and ``app/domain/models/__init__.py`` to
  import and register all new models so that SQLAlchemy recognises
  them.
* Expanded Celery configuration to declare dedicated queues and
  dead‑letter queues for each domain and added routing rules for
  ``created``, ``updated`` and ``deleted`` events per domain.
* Updated the service package initializer to expose all new service
  functions via ``app.domain.services`` for convenient import.
* Enhanced analysis documentation to describe the new models,
  migrations, messaging configuration, schemas, routes and tests.

### Pending

No further pending items remain for the domain implementations.  Future
iterations may focus on adding integration tests, performance tuning or
additional features not covered by the initial DDL.