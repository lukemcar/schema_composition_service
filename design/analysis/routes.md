# Analysis – API Routes

This document summarises the changes made to the FastAPI routing layer to
expose new endpoints for additional domain objects.

## Overview

The API routes are defined in `app/api/routes`.  Each file registers a
router for a specific resource and mounts it under a tenant prefix
(`/tenants/{tenant_id}`) to enforce tenant scoping via the `auth_jwt`
dependency.

## FormCatalogCategory Routes

The file `app/api/routes/form_catalog_category.py` defines a router for
`FormCatalogCategory`.  It introduces endpoints analogous to those in
`schema_composition.py`:

* `GET /tenants/{tenant_id}/form-catalog-categories` – Lists categories
  with pagination.
* `POST /tenants/{tenant_id}/form-catalog-categories` – Creates a new
  category using the `FormCatalogCategoryCreate` schema.
* `GET /tenants/{tenant_id}/form-catalog-categories/{form_catalog_category_id}`
  – Retrieves a specific category.
* `PUT /tenants/{tenant_id}/form-catalog-categories/{form_catalog_category_id}`
  – Updates a category via the `FormCatalogCategoryUpdate` schema.
* `DELETE /tenants/{tenant_id}/form-catalog-categories/{form_catalog_category_id}`
  – Deletes the category.

Each endpoint passes the database session and user context to the service
layer.  Audit fields (`created_by`, `updated_by`) default to the `sub`
claim from the JWT if not provided by the client.

## FieldDef Routes

Similarly, `app/api/routes/field_def.py` registers routes for the
`FieldDef` resource:

* `GET /tenants/{tenant_id}/field-defs` – Lists field definitions for a
  tenant with pagination.
* `POST /tenants/{tenant_id}/field-defs` – Creates a new field definition
  from a `FieldDefCreate` payload.
* `GET /tenants/{tenant_id}/field-defs/{field_def_id}` – Retrieves a
  specific field definition.
* `PUT /tenants/{tenant_id}/field-defs/{field_def_id}` – Updates a field
  definition via `FieldDefUpdate`.
* `DELETE /tenants/{tenant_id}/field-defs/{field_def_id}` – Deletes the
  definition.

These routes call the corresponding service functions and publish events
for create, update and delete operations.

## Main API Registration

`main_api.py` was updated to import and mount the new routers on the
application.  After registering the health and `SchemaComposition` routers, it
includes the `form_catalog_category` and `field_def` routers.  When
additional domains are added, their routers must similarly be imported
and registered to expose the endpoints.

## Additional Routes

After the initial work adding routes for `FormCatalogCategory` and
`FieldDef`, the API layer was expanded to expose full CRUD endpoints
for every remaining domain object defined in the simplified DDL.  The
following routers were added and are registered in `main_api.py`:

* **FieldDefOption** (`field-def-options`) – Endpoints to list,
  create, retrieve, update and delete option values for
  single‑select and multi‑select fields.  Supports optional
  filtering by `field_def_id`.
* **Component** (`components`) – CRUD endpoints for reusable UI
  components.
* **ComponentPanel** (`component-panels`) – CRUD endpoints with
  optional filters by `component_id` and `parent_panel_id`.
* **ComponentPanelField** (`component-panel-fields`) – CRUD
  endpoints linking a `FieldDef` to a `ComponentPanel` with
  optional filters.
* **Form** (`forms`) – CRUD endpoints for form definitions.
* **FormPanel** (`form-panels`) – CRUD endpoints with optional filter
  by `form_id`.
* **FormPanelComponent** (`form-panel-components`) – CRUD endpoints
  representing an embedded component within a form panel.
* **FormPanelField** (`form-panel-fields`) – CRUD endpoints for
  ad hoc fields placed directly on a form panel.
* **FormSubmission** (`form-submissions`) – CRUD endpoints for
  submission envelopes; supports optional filtering by `form_id`.
* **FormSubmissionValue** (`form-submission-values`) – CRUD
  endpoints for individual captured values within a submission;
  supports filtering by `form_submission_id` and
  `field_instance_path`.

Each router follows the same pattern established by earlier
domains: tenant‑scoped prefixes, dependency injection of the database
session and JWT validation, and invocation of service functions to
perform the underlying work.  All routers are registered in
`main_api.py`, ensuring they appear in the generated OpenAPI
specification and are routed through the same middleware stack.