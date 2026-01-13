# Analysis – Pydantic Schemas

This document summarises the modifications and additions to the
`app/domain/schemas` package to support new domain objects defined in the
input DDL.

## Overview

The Pydantic schema layer defines request and response models for the API.
When adding new domain objects, each table receives a set of schemas for
creating, updating and returning records.  Common patterns include:

* A base model containing shared fields and type annotations.
* A `Create` model that defines required fields for POST operations,
  omitting server‑generated fields like primary keys and timestamps.
* An `Update` model allowing partial updates via PUT operations, with all
  fields optional.
* An output model (`Out`) that reads values directly from the SQLAlchemy
  model using `ConfigDict(from_attributes=True)` to simplify mapping.
* A list response wrapper (`ListResponse`) that includes a total count and
  pagination metadata.

## FormCatalogCategory Schemas

The new file `app/domain/schemas/form_catalog_category.py` introduces four
schemas:

* `FormCatalogCategoryCreate` specifies `category_key` and
  `category_name` as required along with optional `description`,
  `is_active` and audit fields.  It is used when creating a new
  category.
* `FormCatalogCategoryUpdate` allows modifying the category via PUT.  All
  fields are optional, enabling partial updates.
* `FormCatalogCategoryOut` mirrors the model and includes all fields.  It
  configures Pydantic to read from SQLAlchemy model instances.
* `FormCatalogCategoryListResponse` wraps a list of
  `FormCatalogCategoryOut` instances with pagination metadata.

These schemas are imported and exposed in the package initializer for
downstream use.

## FieldDef Schemas

To represent the `FieldDef` domain, the file
`app/domain/schemas/field_def.py` defines several models:

* `FieldDefBase` describes the complete set of fields, using the enum
  classes from `enums.py` for `data_type`, `element_type` and
  `source_type`.  Many attributes are optional to support creation and
  updates.
* `FieldDefCreate` inherits from `FieldDefBase` but marks certain fields
  (like `field_def_business_key`, `name`, `field_key` and `label`) as
  required for creation.  It omits server‑generated fields such as
  primary keys and timestamps.
* `FieldDefUpdate` makes all fields optional to enable partial updates via
  PUT.  It includes the audit field `updated_by` for recording the actor.
* `FieldDefOut` inherits from `FieldDefBase` and configures Pydantic to
  populate values from ORM objects.
* `FieldDefListResponse` wraps a list of `FieldDefOut` items with
  pagination metadata.

The schemas support flexible JSONB fields for `validation` and
`ui_config` and preserve type safety via enumerations.

## Event Schemas

The nested `events` package contains message payload definitions for
domain events.  For each domain three message classes are created:
`<Domain>CreatedMessage`, `<Domain>UpdatedMessage` and
`<Domain>DeletedMessage`.  These classes are used by the messaging
layer when publishing events and include the tenant ID and the primary
identifier of the affected record.  In addition to the initial
implementations for `FormCatalogCategory` and `FieldDef`, event
schemas were added for every new domain: `FieldDefOption`,
`Component`, `ComponentPanel`, `ComponentPanelField`, `Form`,
`FormPanel`, `FormPanelComponent`, `FormPanelField`, `FormSubmission`
and `FormSubmissionValue`.

These message schemas ensure type‑safe event envelopes and provide
documentation for downstream consumers about the payload structure.

## Additional Schemas

Beyond the schemas described above, the schema package now includes
models for all remaining tables in the DDL.  Each follows the same
pattern established for `FormCatalogCategory` and `FieldDef`:

* **FieldDefOption** – Defines selectable options for single‑select and
  multi‑select fields.  The base schema captures `option_key`,
  `option_label` and ordering; the output model adds IDs, foreign
  keys and audit fields.  A list response wrapper supports
  pagination.
* **Component** – Models reusable UI components.  Schemas capture the
  component key, version, name, optional description and category,
  configuration JSON and lifecycle flags.  Output models add IDs and
  timestamps.
* **ComponentPanel** – Represents panels nested within a component.
  Schemas include the parent component ID, optional parent panel ID,
  panel key and label, configuration, ordering and audit fields.
* **ComponentPanelField** – Describes a field placed on a component
  panel.  Schemas capture the parent panel ID, field definition ID,
  override configuration, ordering, required flag and audit fields.
* **Form** – Defines top‑level form definitions.  Schemas mirror the
  model’s business keys, name, description, category reference,
  configuration JSON and flags.  Output models include UUIDs and
  timestamps.
* **FormPanel** – Models panels within a form.  Schemas contain the
  parent form ID, optional parent panel ID, panel key and label,
  configuration, ordering and audit fields.
* **FormPanelComponent** – Embeds a reusable component into a form
  panel.  Schemas capture the form panel ID, component ID,
  configuration, ordering and audit metadata.
* **FormPanelField** – Represents an ad hoc field placed directly on a
  form panel.  Schemas include the form panel ID, field definition
  ID, override JSON, ordering, required flag and audit fields.
* **FormSubmission** – Captures a submission envelope for a form.
  Schemas include the form ID, submission status, submission actor
  metadata, deletion flag and audit fields.  Output models include
  timestamps and a boolean `is_deleted` flag.
* **FormSubmissionValue** – Stores individual values within a
  submission.  Schemas capture the submission ID, fully qualified
  field instance path, JSON value and audit fields.

All schemas are exported in `app/domain/schemas/__init__.py` and
imported by the route and service layers.  This comprehensive set of
schemas now provides strong typing across the entire API surface.