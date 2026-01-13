# Analysis – Database Migrations

This document explains the database migration files added to support the
new domain objects from `form_schema_v02.sql`.

## Overview

Database schema changes are managed via Liquibase migrations located under
`migrations/liquibase/sql`.  Each migration file corresponds to a new
table or incremental change.  The root changelog
(`migrations/liquibase/changelog-root.xml`) includes all SQL files in
lexicographic order via the `<includeAll>` directive.  New migrations
must therefore be named sequentially (`002_create_<table>.sql`,
`003_create_<another>.sql`, etc.) to ensure proper ordering.

## New Migrations

Over the course of implementing the full set of domain objects from the
simplified DDL, a sequence of Liquibase migration files were added
under `migrations/liquibase/sql`.  Each migration creates a table and
its accompanying indexes and constraints.  The root changelog
(`changelog-root.xml`) picks up these files automatically via the
`<includeAll>` directive.  The migrations, in order, are:

| Migration File | Description |
|---------------|-------------|
| `002_create_form_catalog_category.sql` | Creates the `form_catalog_category` table with a UUID primary key, tenant‑scoped uniqueness on `category_key` and `category_name`, optional description and active flag, and audit columns. |
| `003_create_field_def.sql` | Defines the `field_def` table with versioned business keys, enumerated data and element types, JSON configuration fields, publication and archiving flags, source metadata and audit columns.  Includes numerous indexes for efficient tenant‑scoped queries. |
| `004_create_field_def_option.sql` | Creates the `field_def_option` table to store allowed select options for field definitions.  Enforces uniqueness of `option_key` and `option_order` per tenant and field definition and records audit metadata. |
| `005_create_component.sql` | Adds the `component` table for reusable UI components.  Defines business keys (`component_key`, `version`), name, optional description, category reference, configuration JSON, active flag and audit fields. |
| `006_create_component_panel.sql` | Establishes `component_panel` to organise panels within a component.  Stores parent panel relationships, panel keys and labels, JSON configuration, ordering and audit fields. |
| `007_create_component_panel_field.sql` | Defines `component_panel_field` to place a field definition on a component panel.  Includes optional override JSON, ordering, required flag and audit information. |
| `008_create_form.sql` | Introduces the `form` table representing top‑level form definitions.  Contains business keys (`form_key`, `version`), form name, optional description, category reference, configuration JSON, active and published flags and audit columns. |
| `009_create_form_panel.sql` | Creates `form_panel` to group form elements into panels.  Supports nesting via `parent_panel_id`, stores panel keys and labels, configuration JSON, ordering and audit metadata. |
| `010_create_form_panel_component.sql` | Defines `form_panel_component` for embedding a reusable component into a form panel.  Records configuration overrides, ordering and audit fields. |
| `011_create_form_panel_field.sql` | Establishes `form_panel_field` for ad hoc placement of a field definition on a form panel.  Includes overrides, ordering, required flag and audit columns. |
| `012_create_form_submission.sql` | Adds the `form_submission` table capturing submission envelopes for forms.  Tracks submission status, optional submission timestamps and actors, deletion flag and audit metadata. |
| `013_create_form_submission_value.sql` | Creates `form_submission_value` storing individual field values within a submission.  Stores fully qualified field instance paths, JSON values and audit information. |

Each migration reproduces the simplified structure from the DDL, using
UUID primary keys, tenant‑scoped constraints and sensible defaults for
booleans and timestamps.  After applying these migrations, all tables
required by the service are present and ready for SQLAlchemy to map.

## Pending Migrations

All tables defined in the simplified DDL are now covered by
migration files.  No further migrations are pending.