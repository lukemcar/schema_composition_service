# Schema vs ORM Alignment Report

**Liquibase file used:** `migrations/liquibase/sql/001_init_schema.sql`

**Tables discovered (14):**
- `schema_composition.component`
- `schema_composition.component_panel`
- `schema_composition.component_panel_field`
- `schema_composition.field_def`
- `schema_composition.field_def_option`
- `schema_composition.form`
- `schema_composition.form_catalog_category`
- `schema_composition.form_panel`
- `schema_composition.form_panel_component`
- `schema_composition.form_panel_field`
- `schema_composition.form_submission`
- `schema_composition.form_submission_archive`
- `schema_composition.form_submission_value`
- `schema_composition.form_submission_value_archive`

**Models found (12):**
- `schema_composition.form_panel_field` → `app/domain/models/form_panel_field.py`
- `schema_composition.form_submission_value` → `app/domain/models/form_submission_value.py`
- `schema_composition.form_catalog_category` → `app/domain/models/form_catalog_category.py`
- `schema_composition.field_def` → `app/domain/models/field_def.py`
- `schema_composition.component_panel_field` → `app/domain/models/component_panel_field.py`
- `schema_composition.component` → `app/domain/models/component.py`
- `schema_composition.component_panel` → `app/domain/models/component_panel.py`
- `schema_composition.form` → `app/domain/models/form.py`
- `schema_composition.field_def_option` → `app/domain/models/field_def_option.py`
- `schema_composition.form_submission` → `app/domain/models/form_submission.py`
- `schema_composition.form_panel` → `app/domain/models/form_panel.py`
- `schema_composition.form_panel_component` → `app/domain/models/form_panel_component.py`

## Updated model details
The following models were updated to align with Liquibase DDL:

- `schema_composition.field_def`: added missing index definitions to `__table_args__` and imported `text` from `sqlalchemy`.
- `schema_composition.field_def_option`: added a case-insensitive label search index and imported `text`.

## Missing models
The following tables defined in the DDL do not have corresponding ORM models:
- `schema_composition.form_submission_archive`
- `schema_composition.form_submission_value_archive`
These tables were noted but not created by this agent.

## Models without matching tables
Every ORM model corresponds to a table in the Liquibase schema.

## Notes
- Some models intentionally use surrogate primary keys and omit certain advanced constraints from the DDL. These simplifications were preserved, and only index definitions were added where critical for query performance.
- This report does not cover other potential differences such as foreign key constraint names or composite primary keys; aligning those would require broader refactoring beyond the scope of this run.