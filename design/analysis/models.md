# Analysis – Domain Models

This analysis document describes the changes made to the domain models in the
project when adding support for new domain objects defined in
`form_schema_v02.sql`.

## Overview

The existing project defined a single domain (`MyEntity`) as an example.  To
support the additional tables in the DDL, we added new SQLAlchemy model classes
and enumerations in the `app/domain/models` package.  Each model mirrors the
structure of its corresponding table in the database and introduces
tenant‑scoped identifiers, audit fields and relevant constraints.

## Enumerations

The DDL defines three enumerated types: `field_data_type`, `field_element_type`
and `artifact_source_type`.  These were implemented once in
`app/domain/models/enums.py` using Python `Enum` classes so that they can be
reused across multiple models.  Defining enums centrally ensures that all
models reference the same enumeration definitions, preventing duplication and
inconsistencies.

## FormCatalogCategory

The `FormCatalogCategory` model was introduced in `app/domain/models/form_catalog_category.py`.
It maps to the `dyno_form.form_catalog_category` table and includes:

* A UUID primary key (`form_catalog_category_id`) and `tenant_id` to enforce
  tenant‑scoping.
* Business fields `category_key` and `category_name` with uniqueness
  constraints per tenant.
* Optional descriptive fields (`description`) and a boolean `is_active` flag.
* Audit fields (`created_at`, `updated_at`, `created_by`, `updated_by`) with
  sensible defaults.

The model inherits from the common `Base` declarative class and defines a
`__repr__` method for debugging.  A composite unique constraint on
`tenant_id` and `id` enforces tenant safety, and additional unique
constraints ensure that category keys and names are unique within a tenant.

## FieldDef

To support the `dyno_form.field_def` table, a `FieldDef` model was added in
`app/domain/models/field_def.py`.  Given the complexity of the table, this
model includes a large number of columns covering versioned identity,
cataloguing metadata, UI configuration, publication/archiving flags and
provenance details.  Key points include:

* `field_def_id` (UUID) as the primary key and `tenant_id` for scoping.
* `field_def_business_key` and `field_def_version` form a tenant‑scoped
  versioned identity; a unique constraint enforces that combination.
* `name`, `description`, `field_key`, `label` and `category_id` represent
  human‑readable metadata and grouping.
* Enumerated fields `data_type`, `element_type` and `source_type` reference
  the enums defined in `enums.py`.
* JSONB fields `validation` and `ui_config` store flexible configuration.
* Publication and archiving flags (`is_published`, `is_archived`) with
  corresponding timestamps and default values.
* Source metadata fields (`source_package_key`, `source_artifact_key`,
  `source_artifact_version`, `source_checksum`, `installed_at`, `installed_by`)
  capture provenance details when a field is installed from the marketplace
  or provider.

Index and unique constraints were faithfully reproduced based on the DDL to
support common lookup patterns (e.g. by `tenant_id`, `field_key`, `category_id`).

## Additional Models

In the final iteration the service was extended to implement models for
all remaining tables in the DDL.  The following SQLAlchemy model
classes were added under `app/domain/models`:

- `FieldDefOption` – stores selectable option values for single‑select
  and multi‑select field definitions.  Unique constraints enforce
  uniqueness of option keys and ordering within a tenant and field
  definition.
- `Component`, `ComponentPanel` and `ComponentPanelField` – define
  reusable UI components, their nested panels and the placement of
  field definitions onto component panels, respectively.
- `Form`, `FormPanel`, `FormPanelComponent` and `FormPanelField` –
  represent form definitions, their nested panels, embedded
  components and ad hoc fields placed directly on a form panel.
- `FormSubmission` and `FormSubmissionValue` – capture submission
  envelopes and individual field values for submitted forms.

Each model follows the established conventions: a UUID primary key,
`tenant_id` for scoping, relevant business keys and labels, optional
JSON configuration fields, ordering integers, lifecycle flags and audit
fields.  Unique constraints and indexes were added to support the
common query patterns anticipated by the API and to preserve tenant
isolation.