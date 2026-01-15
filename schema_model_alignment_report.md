# Schema vs ORM Alignment Report

This report documents the alignment work performed to bring the SQLAlchemy
models in this service in line with the authoritative Liquibase DDL
defined in `migrations/liquibase/sql/001_init_schema.sql`.  All tables,
columns, constraints, and indexes from the DDL were reviewed and the
corresponding ORM models were updated to match exactly.  No surrogate
identities, missing columns, or extra fields remain.  Tenant safety is
respected via composite foreign keys and deferrable unique constraints as
specified in the schema.

**Liquibase file used:** `migrations/liquibase/sql/001_init_schema.sql`

## Tables discovered (14)

The following tables were extracted from the init schema, in order of
appearance.  All tables reside in the `schema_composition` schema unless
otherwise noted.

| # | Table name |
|---|------------|
| 1 | `form_catalog_category` |
| 2 | `field_def` |
| 3 | `field_def_option` |
| 4 | `component` |
| 5 | `component_panel` |
| 6 | `component_panel_field` |
| 7 | `form` |
| 8 | `form_panel` |
| 9 | `form_panel_field` |
|10 | `form_panel_component` |
|11 | `form_submission` |
|12 | `form_submission_value` |
|13 | `form_submission_archive` |
|14 | `form_submission_value_archive` |

## Models found (14)

The repository contains exactly one ORM model for each table.  The
discovered models and their file locations are listed below:

| Table | Model file |
|------|-----------|
| `form_catalog_category` | `app/domain/models/form_catalog_category.py` |
| `field_def` | `app/domain/models/field_def.py` |
| `field_def_option` | `app/domain/models/field_def_option.py` |
| `component` | `app/domain/models/component.py` |
| `component_panel` | `app/domain/models/component_panel.py` |
| `component_panel_field` | `app/domain/models/component_panel_field.py` |
| `form` | `app/domain/models/form.py` |
| `form_panel` | `app/domain/models/form_panel.py` |
| `form_panel_field` | `app/domain/models/form_panel_field.py` |
| `form_panel_component` | `app/domain/models/form_panel_component.py` |
| `form_submission` | `app/domain/models/form_submission.py` |
| `form_submission_value` | `app/domain/models/form_submission_value.py` |
| `form_submission_archive` | `app/domain/models/form_submission_archive.py` |
| `form_submission_value_archive` | `app/domain/models/form_submission_value_archive.py` |

## Updated mappings

The following models were refactored to fully align with the DDL.  Each
update incorporated all columns, data types, defaults, nullability, named
constraints, and indexes from the corresponding table section in the
Liquibase file.  Composite foreign keys were used to enforce tenant
boundaries, and deferrable unique constraints were specified where
indicated in the DDL.

| Table | Updated model |
|------|---------------|
| `component` | `app/domain/models/component.py` |
| `component_panel` | `app/domain/models/component_panel.py` |
| `form` | `app/domain/models/form.py` |
| `form_panel` | `app/domain/models/form_panel.py` |
| `form_panel_field` | `app/domain/models/form_panel_field.py` |
| `form_panel_component` | `app/domain/models/form_panel_component.py` |
| `form_submission` | `app/domain/models/form_submission.py` |
| `form_submission_value` | `app/domain/models/form_submission_value.py` |

Models for `form_catalog_category`, `field_def`, `field_def_option`,
`component_panel_field`, `form_submission_archive`, and
`form_submission_value_archive` were already in parity with the DDL and
required no changes.

## Tables without models

None.  Every table defined in the Liquibase init schema has a
corresponding SQLAlchemy model in the repository.

## Models without matching tables

None.  The repository contains no ORM models that lack a counterpart in
the Liquibase schema.

## Per‑table alignment summary

Below is a high‑level summary of notable fixes applied during the
alignment process.  Every column, constraint, and index from the DDL is
represented in the updated models.  Where applicable, partial indexes
with `postgresql_where` clauses, GIN indexes, and deferrable unique
constraints were implemented.

### `component`

- Added missing primary key column `id` (UUID) and all metadata columns
  (`component_business_key`, `component_version`, `name`, `description`,
  `component_key`, `component_label`, `category_id`, `ui_config`, lifecycle
  flags, provenance fields, audit fields).
- Implemented all check constraints from the DDL: positive version,
  non‑blank business key, component key, and name, correct formatting for
  source checksums, and consistency between lifecycle flags and their
  timestamps.
- Added composite foreign key to `form_catalog_category` for the optional
  `category_id` reference with `ON DELETE SET NULL` behavior.
- Added unique constraints for versioned business identity and stable
  runtime identity within a tenant.
- Added all indexes, including partial index on
  `(tenant_id, category_id, name)` conditioned on `category_id IS NOT NULL`.
- Declared the table schema as `schema_composition`.

### `component_panel`

- Added `id` (primary key), `tenant_id`, `component_id`, `parent_panel_id`,
  `panel_key`, `panel_label`, `ui_config`, `panel_actions`, and full audit
  columns.
- Implemented check constraints enforcing non‑blank panel keys/labels and
  prohibiting self‑parenting.
- Added composite unique constraints for `(tenant_id, id)`,
  `(tenant_id, component_id, panel_key)`, and `(tenant_id, component_id)`.
- Added tenant‑safe foreign keys to `component` and self‑referencing
  `parent_panel_id`.
- Added indexes for parent lookups and recency queries.

### `form`

- Added missing columns for business identity (`form_business_key`,
  `form_version`, `name`, `description`, `form_key`, `form_label`,
  `category_id`, `ui_config`, lifecycle flags, provenance fields) and full
  audit metadata.
- Implemented check constraints for positive version, non‑blank business
  key/key/label, consistency of lifecycle timestamps, and source checksum
  formatting.
- Added composite foreign key to `form_catalog_category`.
- Added unique constraints for versioned business identity and stable
  runtime identity within a tenant.
- Added indexes on `(tenant_id, name)`, a functional index on
  `lower(name)` for case‑insensitive lookups, an index on catalog
  state, and a composite index on source keys.

### `form_panel`

- Added `id`, `tenant_id`, `form_id`, `panel_key`, `panel_label`, `ui_config`,
  and full audit columns.
- Implemented check constraints for non‑blank keys/labels.
- Added composite unique constraints for `(tenant_id, id)`, and
  `(tenant_id, form_id, panel_key)`.
- Added tenant‑safe foreign key to `form`.
- Added indexes for `(tenant_id, form_id)` and for recency queries on
  `(tenant_id, form_id, updated_at)`.

### `form_panel_field`

- Added numerous columns: `field_order`, `ui_config`, `field_config`,
  `field_config_hash`, `source_field_def_hash`, `last_imprinted_at`, and
  audit metadata.
- Implemented multiple check constraints enforcing non‑negative order,
  SHA‑256 hash formats, and JSON schema validation on `field_config` via
  `public.jsonb_matches_schema`.
- Added unique constraints for `(tenant_id, id)`,
  `(tenant_id, panel_id, field_def_id)`, and `(tenant_id, panel_id, field_order)`.
- Added tenant‑safe foreign keys to `form_panel` and `field_def`.
- Added indexes for lookups by field definition, recency queries, and
  combined hashes.

### `form_panel_component`

- Added missing columns: `id`, `tenant_id`, `panel_id`, `component_id`,
  `component_order`, `config`, `nested_overrides`, and audit metadata.
- Implemented check constraints for non‑negative ordering, SHA‑256 hash
  format, and JSON schema validation of `nested_overrides` via
  `public.jsonb_matches_schema`.
- Added unique constraints for `(tenant_id, id)`,
  `(tenant_id, panel_id, component_id)`, and `(tenant_id, panel_id, component_order)`.
- Added tenant‑safe foreign keys to `form_panel` and `component`.
- Added indexes for component lookups, recency queries, and combined
  hashes.

### `form_submission`

- Added primary key `id` and full lifecycle columns
  (`is_submitted`, `submitted_at`, `submission_version`, `is_archived`,
  `archived_at`) along with audit metadata.
- Implemented check constraints enforcing non‑negative submission_version
  and consistency between draft/submitted states and the corresponding
  timestamps.
- Added unique constraint `(tenant_id, id)`.
- Added tenant‑safe foreign key to `form`.
- Added indexes for form lookups and recency queries.

### `form_submission_value`

- Completely replaced the prior simplified model with a full
  representation: added `id`, `tenant_id`, `form_submission_id`,
  `field_def_id`, `field_path` (VARCHAR(800)), placement references
  (`form_panel_field_id`, `form_panel_component_id`, `component_panel_field_id`),
  the JSONB `value`, `value_search_text` (TEXT), and audit fields.
- Implemented a comprehensive JSON schema check constraint using
  `public.jsonb_matches_schema` to validate the `value` structure when
  present, allowing for multiple field data types and enforcing limits on
  multiselect arrays.
- Added check constraints to enforce non‑blank paths, correct
  dot‑separated formatting of `field_path`, and exclusivity of placement
  references (exactly one path must be set).
- Added deferrable unique constraints for
  `(tenant_id, form_submission_id, field_path)`,
  `(tenant_id, form_submission_id, form_panel_field_id)`, and
  `(tenant_id, form_submission_id, form_panel_component_id, component_panel_field_id)`.
- Added tenant‑safe foreign keys to `form_submission`, `field_def`,
  `form_panel_field`, `form_panel_component`, and `component_panel_field`.
- Added a suite of indexes: tenant scoping, submission lookups,
  field‑path lookups, field definition filtering, partial indexes for
  direct and component placements, a GIN index on the JSONB `value` for
  efficient searching, and recency queries.

### Archive tables

Models for `form_submission_archive` and `form_submission_value_archive`
were already consistent with the DDL and were left unchanged.

## Unresolved issues

No unresolved schema alignment issues remain.  All ORM models now match
their corresponding DDL definitions exactly, including column names,
types, defaults, nullability, foreign key relationships, check and
unique constraints, and indexes.
