# Analysis – Service Layer

This document details the service layer additions for the new domains
introduced from `form_schema_v02.sql`.  The service layer encapsulates
business logic, coordinates persistence and publishes domain events via
Celery.

## Overview

For each domain the service module exports functions to create, retrieve,
list, update and delete records.  Functions accept a SQLAlchemy `Session`, a
tenant ID and domain‑specific parameters.  They raise `HTTPException`
instances on error and return model instances on success.  Events are
published only after successful commits to avoid out‑of‑sync messages.

## FormCatalogCategory Service

The `form_catalog_category_service.py` module implements CRUD operations for
categories:

* `create_form_catalog_category` – Constructs a `FormCatalogCategory`
  instance, sets audit fields and commits it.  After commit it publishes a
  `form-catalog-category.created` event via Celery using the
  `FormCatalogCategoryProducer`.
* `get_form_catalog_category` – Retrieves a category by primary key and
  tenant ID, raising a 404 if not found or cross‑tenant.
* `list_form_catalog_categories` – Queries all categories for a tenant
  with pagination.  It returns the items and the total count as a tuple.
* `update_form_catalog_category` – Applies updates to a category if
  provided and records the changes.  If any fields change, a
  `form-catalog-category.updated` event is emitted with the changed
  fields and the updated object payload.
* `delete_form_catalog_category` – Deletes the category and publishes a
  deletion event.

The service uses defensive logging and wraps database errors in
`HTTPException` instances to provide consistent error responses.

## FieldDef Service

The `field_def_service.py` module performs analogous operations for the
`FieldDef` domain.  Given the larger number of columns, the update
function collects changed fields across numerous attributes before
committing.  Important behaviours include:

* Enforcement of tenant scope when retrieving and modifying records.
* Publication of events with complete payloads and change summaries via
  `FieldDefProducer`.
* Proper handling of audit fields (`created_by`, `updated_by`) and
  timestamps.

As with categories, listing returns both items and the total count to
support paginated responses.

## Additional Services

After the initial implementation of `FormCatalogCategory` and `FieldDef`,
the service layer was expanded to cover all remaining domains.  New
service modules include:

- **FieldDefOption Service** (`field_def_option_service.py`) – CRUD
  operations for allowed option values, with optional filtering by
  `field_def_id` when listing.
- **Component Services** – Modules `component_service.py`,
  `component_panel_service.py` and `component_panel_field_service.py`
  manage reusable UI components, their nested panels and the placement
  of field definitions onto component panels, respectively.
- **Form Services** – Modules `form_service.py`, `form_panel_service.py`,
  `form_panel_component_service.py` and `form_panel_field_service.py`
  implement CRUD logic for form definitions, nested panels, embedded
  components and ad hoc fields placed directly on a form panel.
- **Submission Services** – Modules `form_submission_service.py` and
  `form_submission_value_service.py` provide endpoints to create, list,
  retrieve, update and delete submission envelopes and the individual
  values captured within a submission.  Listing functions offer
  optional filters by `form_id`, `form_submission_id` or
  `field_instance_path`.

Each service follows the established conventions: verifying tenant
ownership on reads and writes, recording changes for update events,
committing transactions before emitting events, and capturing audit
metadata.  This comprehensive service layer now covers all tables
defined in the simplified DDL, enabling full CRUD operations via the
API.