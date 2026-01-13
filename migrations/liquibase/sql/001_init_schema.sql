-- ======================================================================
-- Updated Schema Composition DDL Marketplace-Grade Hardening and Additions
-- ======================================================================
--
-- This script inlines the original form_schema.sql and augments it with
-- marketplace-grade hardening. Corrections include missing constraints,
-- tenant-safe foreign keys, additional indexes for common access patterns,
-- verbose documentation, provenance metadata columns, stable instance
-- identifiers for embedded component placements, and deterministic JSONB
-- merge utilities.
--
-- ----------------------------------------------------------------------
-- Original schema definitions (inlined)
-- ----------------------------------------------------------------------
-- BEGIN original form_schema.sql
-- ======================================================================
-- Dyno FROMs – Field and Component Catalog Schema with Form Definitions
-- ======================================================================
-- liquibase formatted sql
-- changeset crm_service:002_support_domain_schema
--
-- PURPOSE
--
-- KEY ARCHITECTURE DECISIONS
--
-- SECURITY / TENANCY
--
-- ======================================================================

SET search_path TO public, dyno_form;



-- ======================================================================
-- Dyno CRM - Field Catalog (Data Type vs Element Type)
-- ======================================================================
-- PURPOSE
--   These objects define reusable, tenant-scoped field definitions that
--   can be used by tickets (and later by other entities).
--
--   This design separates:
--     1) data_type    - the shape of the value stored (semantic type)
--     2) element_type - how the field is rendered or behaves in the UI
--
--   IMPORTANT
--     - ACTION is an element_type (behavior), not a data_type.
--     - SELECT/MULTISELECT are element types; the underlying data is a
--       reference to option keys (single value vs array).
--
-- NOTES
--   - validation and ui_config are intentionally flexible JSONB blobs.
--   - If you later want JSON schema enforcement, add CHECK constraints
--     using public.jsonb_matches_schema(...) as you already do elsewhere.
-- ======================================================================
-- ----------------------------------------------------------------------
-- Enum: field_data_type
-- ----------------------------------------------------------------------
-- PURPOSE
--   Defines the semantic data shape stored for a field.
--
-- GUIDELINE
--   Do not put UI widgets here (radio, checkbox, button, etc.).
--   Those belong to field_element_type or ui_config.
-- ----------------------------------------------------------------------

DO $$ BEGIN
    CREATE TYPE dyno_form.field_data_type AS ENUM (
        'TEXT',
        'NUMBER',
        'BOOLEAN',
        'DATE',
        'DATETIME',
        'SINGLESELECT',  -- stores one option_key
        'MULTISELECT'    -- stores an array of option_key values
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ----------------------------------------------------------------------
-- Enum: field_element_type
-- ----------------------------------------------------------------------
-- PURPOSE
--   Defines how the field is rendered or behaves in the UI.
--
-- NOTES
--   - ACTION is a UI element that triggers behavior and does not store
--     a value. When element_type=ACTION, data_type should be NULL.
--   - SELECT/MULTISELECT represent UI widgets. Their stored data shape is
--     described by field_data_type (SINGLESELECT/MULTISELECT).
-- ----------------------------------------------------------------------

DO $$ BEGIN
    CREATE TYPE dyno_form.field_element_type AS ENUM (
        'TEXT',
        'TEXTAREA',
        'DATE',
        'DATETIME',
        'SELECT',
        'MULTISELECT',
        'ACTION'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;




-- ----------------------------------------------------------------------
-- Enum: artifact_source_type
-- ----------------------------------------------------------------------
-- PURPOSE
--   Classifies the provenance of a marketplace artifact installed for a tenant.
DO $$ BEGIN
    CREATE TYPE dyno_form.artifact_source_type AS ENUM (
        'MARKETPLACE', 'PROVIDER', 'TENANT', 'SYSTEM'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;


-- ----------------------------------------------------------------------
-- Table: dyno_form.form_catalog_category
-- ----------------------------------------------------------------------
-- PURPOSE
--   Tenant-scoped category used to organize reusable form elements (field
--   definitions and components) in builder UI palettes (accordion/grouping).
--
-- CORE CONCEPTS
--   - category_key:
--       Stable tenant-scoped identifier used for import/export and integrations.
--   - category_name:
--       Human-readable label shown in builder UI.
--   - is_active:
--       Controls whether the category is available for selection/use in UI.
--
-- IMPORTANT INVARIANTS
--   - tenant_id scopes categories to a tenant boundary.
--   - category_key is unique per tenant.
--   - category_name is unique per tenant (prevents confusing duplicates in UI).
--   - updated_at is maintained by application code or a DB trigger (not included here).
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_form.form_catalog_category (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    category_key VARCHAR(200) NOT NULL,  -- unique per tenant, stable identifier
    category_name VARCHAR(50) NOT NULL,  -- unique per tenant, UI label

    description VARCHAR(200),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Supports tenant-safe composite foreign keys from child tables.
    CONSTRAINT ux_form_catalog_category_id_tenant 
        UNIQUE (tenant_id, id),

    -- Prevent blank/whitespace identifiers.
    CONSTRAINT ck_form_catalog_category_key_nonblank
        CHECK (length(btrim(category_key)) > 0),

    CONSTRAINT ck_form_catalog_category_name_nonblank
        CHECK (length(btrim(category_name)) > 0),

    -- Stable key uniqueness within tenant.
    CONSTRAINT uq_form_catalog_category_tenant_key
        UNIQUE (tenant_id, category_key),

    -- UI label uniqueness within tenant.
    CONSTRAINT uq_form_catalog_category_tenant_name
        UNIQUE (tenant_id, category_name)
);

-- ----------------------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------------------

-- Common builder query: active categories per tenant.
CREATE INDEX IF NOT EXISTS ix_form_catalog_category_tenant_active
    ON dyno_form.form_catalog_category (tenant_id, is_active);

-- Optional: search by name in admin/builder UI.
CREATE INDEX IF NOT EXISTS ix_form_catalog_category_tenant_name_lower
    ON dyno_form.form_catalog_category (tenant_id, lower(category_name));

-- ----------------------------------------------------------------------
-- Comments
-- ----------------------------------------------------------------------

COMMENT ON TABLE dyno_form.form_catalog_category IS
'Tenant-scoped category used to organize reusable builder palette elements (field definitions and components). Intended for UI grouping (accordion) and marketplace browsing.';

COMMENT ON COLUMN dyno_form.form_catalog_category.id IS
'Primary row identifier (UUID). Immutable technical identity.';

COMMENT ON COLUMN dyno_form.form_catalog_category.tenant_id IS
'Tenant boundary. Categories are tenant-scoped for isolation and customization.';

COMMENT ON COLUMN dyno_form.form_catalog_category.category_key IS
'Stable tenant-scoped identifier for the category (used for import/export and marketplace alignment).';

COMMENT ON COLUMN dyno_form.form_catalog_category.category_name IS
'Human-readable category label shown in builder UI (unique within tenant).';

COMMENT ON COLUMN dyno_form.form_catalog_category.description IS
'Optional description shown in admin/builder UI.';

COMMENT ON COLUMN dyno_form.form_catalog_category.is_active IS
'When true, category is available for selection/use in builder UI; when false it is hidden/disabled.';

COMMENT ON COLUMN dyno_form.form_catalog_category.created_at IS
'Row creation timestamp.';

COMMENT ON COLUMN dyno_form.form_catalog_category.updated_at IS
'Row last-updated timestamp. Typically maintained by application code or a trigger.';

COMMENT ON COLUMN dyno_form.form_catalog_category.created_by IS
'Optional actor identifier (username/service) that created the row.';

COMMENT ON COLUMN dyno_form.form_catalog_category.updated_by IS
'Optional actor identifier (username/service) that last updated the row.';



-- ----------------------------------------------------------------------
-- Table: dyno_form.field_def
-- ----------------------------------------------------------------------
-- PURPOSE
--   Defines a reusable field definition (catalog entry) for a tenant.
--
-- HOW THIS TABLE IS USED
--   This table represents the canonical "catalog artifact" for a field, which can be:
--     - placed into reusable components (composition layer snapshots it)
--     - placed directly onto forms (composition layer snapshots it)
--     - installed from provider defaults or marketplace packages (artifact import)
--
-- CORE CONCEPTS
--   Artifact identity (versioned, immutable conceptually):
--     - field_def_business_key + field_def_version defines the versioned identity
--       of the catalog artifact within a tenant.
--     - field_def_business_key is intended to be immutable after creation
--       (immutability is typically enforced by application rules or a trigger).
--
--   Default key vs instance overrides:
--     - field_key is a default/suggested key for the field definition.
--     - field_key is NOT tenant-unique because downstream placements may override
--       the effective field key/name in imprinted configs or placement overrides.
--     - field_key remains nonblank and indexed for lookup/search.
--
--   Category grouping:
--     - category_id optionally groups this field definition into a tenant-defined
--       builder palette category (accordion grouping / catalog browsing).
--
--   Type system:
--     - data_type describes the stored value shape (semantic type).
--     - element_type describes UI rendering/behavior.
--
-- ACTION ELEMENTS
--   - element_type = ACTION means this entry is an action/button element,
--     not a data-capturing field.
--   - For ACTION elements:
--       * data_type MUST be NULL
--       * validation SHOULD be NULL
--       * ui_config contains action configuration (what it does)
--
-- NON-ACTION ELEMENTS
--   - element_type != ACTION means this entry captures data.
--   - For non-action elements:
--       * data_type MUST be NOT NULL
--
-- SELECT / MULTISELECT
--   - element_type SELECT      -> data_type must be SINGLESELECT
--   - element_type MULTISELECT -> data_type must be MULTISELECT
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_form.field_def (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,

    -- Versioned artifact identity (tenant-scoped)
    field_def_business_key VARCHAR(400) NOT NULL,
    field_def_version INTEGER NOT NULL DEFAULT 1,

    -- Human-readable name for admin/catalog UI.
    name VARCHAR(100) NOT NULL,

    -- Human-readable description for admin/catalog UI.
    description VARCHAR(1000),

    -- Default/suggested key for the field definition.
    -- NOTE: This is NOT tenant-unique. Placements may override the effective key.
    field_key VARCHAR(100) NOT NULL,

    -- Human-readable label shown in UI.
    label VARCHAR(255) NOT NULL,

    -- Optional category used by builder UI to group fields in palettes (accordion).
    category_id UUID,

    -- Semantic data shape stored for this field.
    -- NULL only when element_type=ACTION.
    data_type dyno_form.field_data_type,

    -- UI element type for rendering / behavior.
    element_type dyno_form.field_element_type NOT NULL,

    -- Optional JSON configuration for validation rules (data fields only).
    validation JSONB,

    -- Optional JSON configuration for UI hints and behavior.
    -- For ACTION elements, contains action configuration.
    ui_config JSONB,

    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    published_at TIMESTAMPTZ,

    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    archived_at TIMESTAMPTZ,

    -- ------------------------------------------------------------------
    -- Provenance / source metadata (artifact origin)
    -- ------------------------------------------------------------------

    -- Identifies the origin of this artifact at the time it was created
    -- or installed into the tenant space.
    --
    -- This value distinguishes whether the artifact originated from:
    --   - the built-in system catalog
    --   - a provider-distributed default set
    --   - a marketplace package
    --   - or was created locally by the tenant
    --
    -- Examples:
    --   - SYSTEM       (platform-internal artifact)
    --   - PROVIDER     (default artifact shipped by the service owner)
    --   - MARKETPLACE  (installed from the public or private marketplace)
    --   - TENANT       (created directly within the tenant environment)
    --
    -- Used for:
    --   - builder palette filtering and grouping
    --   - governance and permission enforcement
    --   - upgrade and compatibility workflows
    --   - artifact lifecycle management
    --   - support, audit, and operational diagnostics
    --
    -- This value is set at creation or install time and should be treated
    -- as immutable for the lifetime of the artifact.
    source_type dyno_form.artifact_source_type,

    -- ------------------------------------------------------------------
    -- Provenance / source metadata (immutable imports)
    -- ------------------------------------------------------------------

    -- Identifies the package from which this field definition was installed.
    --
    -- Examples:
    --   - marketplace package key
    --   - provider-distributed bundle identifier
    --
    -- Used for:
    --   - lineage tracking
    --   - dependency resolution
    --   - uninstall / upgrade orchestration
    --   - support and audit diagnostics
    --
    -- This value is immutable once installed.
    source_package_key VARCHAR(400),

    -- Identifies the specific artifact within the source package.
    --
    -- This is the stable identity of the field definition *inside* the package,
    -- independent of tenant-local UUIDs.
    --
    -- Used for:
    --   - mapping installed artifacts back to their catalog definitions
    --   - matching upgrade candidates
    --   - detecting duplicate installs
    --
    -- This value is immutable once installed.
    source_artifact_key VARCHAR(400),

    -- Version identifier of the source artifact at the time of installation.
    --
    -- This is a publisher-controlled version string (not necessarily numeric),
    -- such as:
    --   - "1.0.0"
    --   - "2024.10"
    --   - "v3"
    --
    -- Used for:
    --   - upgrade eligibility checks
    --   - compatibility validation
    --   - reproducibility and audit
    --
    -- This value represents the installed version and does not change unless
    -- the artifact is explicitly upgraded.
    source_artifact_version VARCHAR(100),

    -- Cryptographic checksum (typically SHA-256 hex) of the source artifact
    -- content at install time.
    --
    -- Used for:
    --   - integrity verification
    --   - detecting publisher-side changes without version bumps
    --   - reproducible installs
    --   - forensic and support analysis
    --
    -- Because imported artifacts are immutable, this checksum represents
    -- both the source and effective content.
    source_checksum VARCHAR(64),

    -- Timestamp when this field definition artifact was installed into the tenant.
    --
    -- Used for:
    --   - audit trails
    --   - support diagnostics
    --   - upgrade sequencing
    --   - lifecycle analysis
    installed_at TIMESTAMPTZ,

    -- Identifier of the actor (user, service, or automation) that performed
    -- the installation.
    --
    -- Examples:
    --   - admin username
    --   - system bootstrap service
    --   - marketplace installer service
    installed_by VARCHAR(100)


    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Supports tenant-safe composite foreign keys from child tables.
    CONSTRAINT ux_field_def_id_tenant UNIQUE (tenant_id, id),

    -- Versioned artifact identity must be unique per tenant.
    CONSTRAINT uq_field_def_tenant_business_key_version
        UNIQUE (tenant_id, field_def_business_key, field_def_version),

    -- Tenant-safe FK to builder palette category.
    CONSTRAINT fk_field_def_category_tenant
        FOREIGN KEY (tenant_id, category_id)
        REFERENCES dyno_form.form_catalog_category (tenant_id, id)
        ON DELETE SET NULL,

    -- Business key must not be blank/whitespace.
    CONSTRAINT ck_field_def_business_key_nonblank
        CHECK (length(btrim(field_def_business_key)) > 0),

    -- Version must be positive.
    CONSTRAINT ck_field_def_version_positive
        CHECK (field_def_version >= 1),

    -- Prevent blank/whitespace field_key.
    CONSTRAINT chk_field_def_field_key_not_blank
        CHECK (length(btrim(field_key)) > 0),

    -- Prevent blank/whitespace label.
    CONSTRAINT chk_field_def_label_not_blank
        CHECK (length(btrim(label)) > 0),

    -- Enforce ACTION vs non-ACTION semantics.
    CONSTRAINT chk_field_def_action_requires_no_data_type
        CHECK (
            (element_type = 'ACTION' AND data_type IS NULL)
            OR
            (element_type <> 'ACTION' AND data_type IS NOT NULL)
        ),

    -- Enforce SELECT pairing between element_type and data_type.
    CONSTRAINT chk_field_def_select_data_type_alignment
        CHECK (
            (element_type = 'SELECT' AND data_type = 'SINGLESELECT')
            OR
            (element_type = 'MULTISELECT' AND data_type = 'MULTISELECT')
            OR
            (element_type NOT IN ('SELECT', 'MULTISELECT'))
        ),

    CONSTRAINT ck_field_def_source_checksum_format
        CHECK (source_checksum IS NULL OR source_checksum ~ '^[0-9a-f]{64}$')

);

-- ----------------------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------------------

-- Lookup/filter by default field key within tenant (NOT unique).
CREATE INDEX IF NOT EXISTS ix_field_def_tenant_field_key
    ON dyno_form.field_def (tenant_id, field_key);

-- Builder palette filtering: list field defs by tenant and category.
CREATE INDEX IF NOT EXISTS ix_field_def_tenant_category
    ON dyno_form.field_def (tenant_id, category_id)
    WHERE category_id IS NOT NULL;

-- Common catalog filtering: list field defs by tenant and element type.
CREATE INDEX IF NOT EXISTS ix_field_def_tenant_element_type
    ON dyno_form.field_def (tenant_id, element_type);

-- Common catalog filtering: list field defs by tenant and data type.
CREATE INDEX IF NOT EXISTS ix_field_def_tenant_data_type
    ON dyno_form.field_def (tenant_id, data_type)
    WHERE data_type IS NOT NULL;

-- Optional: search by label in admin UI.
CREATE INDEX IF NOT EXISTS ix_field_def_tenant_label
    ON dyno_form.field_def (tenant_id, lower(label));

-- Optional: search within category by label in builder UI.
CREATE INDEX IF NOT EXISTS ix_field_def_tenant_category_label
    ON dyno_form.field_def (tenant_id, category_id, lower(label))
    WHERE category_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_field_def_tenant_source_type
    ON dyno_form.field_def (tenant_id, source_type);

CREATE INDEX IF NOT EXISTS ix_field_def_tenant_source_keys
    ON dyno_form.field_def (tenant_id, source_package_key, source_artifact_key, source_artifact_version);

-- ----------------------------------------------------------------------
-- Comments
-- ----------------------------------------------------------------------

COMMENT ON TABLE dyno_form.field_def IS
'Reusable tenant-scoped field definition catalog artifact. Supports versioned artifact identity (field_def_business_key + field_def_version) for safe evolution and marketplace alignment. field_key is a default/suggested key that may be overridden at placement time and is therefore not tenant-unique.';

COMMENT ON COLUMN dyno_form.field_def.id IS
'Primary row identifier (UUID). Immutable technical identity.';

COMMENT ON COLUMN dyno_form.field_def.tenant_id IS
'Tenant boundary. All field definitions are tenant-scoped for isolation, access control, and customization.';

COMMENT ON COLUMN dyno_form.field_def.field_def_business_key IS
'Versioned artifact identity key (tenant-scoped). Intended to be immutable after creation. Used to align installs/upgrades across provider/marketplace packages. Uniqueness is enforced together with field_def_version per tenant.';

COMMENT ON COLUMN dyno_form.field_def.field_def_version IS
'Version number for the artifact identified by (tenant_id, field_def_business_key). Must be >= 1. New versions represent new releases of the same conceptual field definition.';

COMMENT ON COLUMN dyno_form.field_def.name IS
'Human-readable internal/admin name for the field definition (catalog display).';

COMMENT ON COLUMN dyno_form.field_def.description IS
'Optional human-readable description for catalog/admin tooling.';

COMMENT ON COLUMN dyno_form.field_def.field_key IS
'Default/suggested key for this field definition. Used as a starting point for builder/runtime, but may be overridden in placement-level configs or imprinted snapshots; therefore it is NOT tenant-unique. Indexed for lookup/filtering.';

COMMENT ON COLUMN dyno_form.field_def.label IS
'Human-readable label shown in UI by default. Placements may override label in imprinted configs/overrides.';

COMMENT ON COLUMN dyno_form.field_def.category_id IS
'Optional reference to dyno_form.form_catalog_category used to group field definitions in builder palette UI (accordion/categories). Tenant-local classification only.';

COMMENT ON COLUMN dyno_form.field_def.data_type IS
'Semantic data shape stored for this field. Must be NULL only when element_type is ACTION; otherwise required.';

COMMENT ON COLUMN dyno_form.field_def.element_type IS
'UI rendering/behavior type for this field definition (TEXT, TEXTAREA, SELECT, ACTION, etc.).';

COMMENT ON COLUMN dyno_form.field_def.validation IS
'Optional JSONB validation rules for data-capturing fields. Typically NULL for ACTION elements.';

COMMENT ON COLUMN dyno_form.field_def.ui_config IS
'Optional JSONB UI hints and behavior configuration. For ACTION elements, contains action configuration (what the action does).';

COMMENT ON COLUMN dyno_form.field_def.is_published IS
'When true, field definition is available in catalog/builder surfaces for selection/use.';

COMMENT ON COLUMN dyno_form.field_def.published_at IS
'Timestamp when the field definition was published (if tracked by application/workflow).';

COMMENT ON COLUMN dyno_form.field_def.is_archived IS
'When true, field definition is archived and should not be offered for new use, but is retained for history/back-compat.';

COMMENT ON COLUMN dyno_form.field_def.archived_at IS
'Timestamp when the field definition was archived (if tracked by application/workflow).';

COMMENT ON COLUMN dyno_form.field_def.created_at IS
'Row creation timestamp.';

COMMENT ON COLUMN dyno_form.field_def.updated_at IS
'Row last-updated timestamp. Typically maintained by application code or a trigger.';

COMMENT ON COLUMN dyno_form.field_def.created_by IS
'Optional actor identifier (username/service) that created the row.';

COMMENT ON COLUMN dyno_form.field_def.updated_by IS
'Optional actor identifier (username/service) that last updated the row.';

----

COMMENT ON COLUMN dyno_form.field_def.source_type IS
'Identifies the origin of this artifact at creation or installation time. Distinguishes system-provided, provider-distributed, marketplace-installed, and tenant-created artifacts. Used for governance, builder palette filtering, upgrade and compatibility workflows, lifecycle management, and audit diagnostics. This value is intended to be immutable once set.';


-- ----------------------------------------------------------------------
-- Table: field_def_option
-- ----------------------------------------------------------------------
-- PURPOSE
--   Defines the allowed options for SELECT / MULTISELECT ticket fields.
--
-- CORE CONCEPTS
--   - Each option belongs to exactly one field_def.
--   - option_key is a stable key for API payloads and integrations.
--   - option_label is the UI display value.
--   - option_order controls UI ordering.
--
-- IMPORTANT
--   - Options are only semantically valid when field_type is SELECT or
--     MULTISELECT. Enforcing that strictly at the DB level requires a
--     trigger (because it depends on the parent row's field_type).
--   - This table still enforces strong tenant-safe FK integrity and
--     uniqueness within a field definition.
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_form.field_def_option (
    -- Composite identity: options are tenant-scoped and belong to a field.
    tenant_id UUID NOT NULL,
    field_def_id UUID NOT NULL,

    -- Stable key used in API values (preferred over display text).
    -- Example: "high", "medium", "low"
    option_key VARCHAR(200) NOT NULL,

    -- Display value shown in UI.
    -- Example: "High", "Medium", "Low"
    option_label VARCHAR(400) NOT NULL,

    -- Controls ordering in dropdown/multi-select UI.
    option_order INTEGER NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    -- Composite primary key for the option row.
    CONSTRAINT pk_field_def_option PRIMARY KEY (tenant_id, field_def_id, option_key),

    -- Tenant-safe FK back to the field definition.
    CONSTRAINT fk_field_def_option_field_def
        FOREIGN KEY (tenant_id, field_def_id)
        REFERENCES dyno_form.field_def (tenant_id, id)
        ON DELETE CASCADE
        DEFERRABLE INITIALLY DEFERRED,

    -- Prevent blank/whitespace keys.
    CONSTRAINT chk_field_def_option_key_not_blank
        CHECK (length(btrim(option_key)) > 0),

    -- Prevent blank/whitespace values.
    CONSTRAINT chk_field_def_option_label_not_blank
        CHECK (length(btrim(option_label)) > 0),

    -- option_order should be non-negative (0-based or 1-based both allowed).
    CONSTRAINT chk_field_def_option_order_non_negative
        CHECK (option_order >= 0)
);

-- Ensure option_order is unique within a field definition (stable ordering).
CREATE UNIQUE INDEX IF NOT EXISTS ux_field_def_option_order
    ON dyno_form.field_def_option (tenant_id, field_def_id, option_order);

-- Optional: look up by display value (useful for admin search, rarely needed).
CREATE INDEX IF NOT EXISTS ix_field_def_option_label
    ON dyno_form.field_def_option (tenant_id, lower(option_label));


-- ----------------------------------------------------------------------
-- Table: dyno_form.component
-- ----------------------------------------------------------------------
-- PURPOSE
--   Represents a reusable, catalog-style "component" that can be added to a form panel.
--   Components are intended to be sourced from:
--     - provider preloaded components (tenant-owned by provider or seeded per-tenant)
--     - marketplace components (distributed templates/components)
--     - tenant-defined components (tenant-created)
--
-- CORE CONCEPTS
--   - Business identity vs. row identity:
--       * id is the immutable row identifier (UUID PK).
--       * component_business_key + component_version provides a stable catalog identity for
--         versioned releases of the same conceptual component.
--   - Stable key vs. UI label:
--       * component_key is a stable, tenant-scoped identifier used in APIs/automation.
--       * component_label is the user-facing label shown in UI.
--   - category_id optionally groups this component into a tenant-defined builder palette
--     category (accordion grouping / catalog browsing).
--   - ui_config is intentionally flexible JSONB for UI hints and runtime behavior.
--
-- IMPORTANT INVARIANTS
--   - tenant_id scopes all data to a tenant boundary.
--   - component_key is unique per tenant (stable identifier).
--   - component_business_key + component_version is unique per tenant (versioned identity).
--   - category_id (when present) must reference a category in the same tenant.
--   - Publishing / archiving timestamps are consistent with their flags:
--       * is_published = true  => published_at is not null
--       * is_published = false => published_at is null
--       * is_archived = true   => archived_at is not null
--       * is_archived = false  => archived_at is null
--   - updated_at is maintained by application code or a DB trigger (not included here).
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_form.component (
    -- ------------------------------------------------------------------
    -- Primary identity
    -- ------------------------------------------------------------------
    id UUID PRIMARY KEY,

    -- Tenant boundary. This table is always tenant-scoped.
    tenant_id UUID NOT NULL,

    -- ------------------------------------------------------------------
    -- Catalog identity (versioning)
    -- ------------------------------------------------------------------
    -- Stable "catalog/business" key used to identify a component across versions
    -- within the same tenant (and potentially across tenants via marketplace import).
    component_business_key VARCHAR(400) NOT NULL,

    -- Monotonic version number for a given (tenant_id, component_business_key).
    -- Typically starts at 1.
    component_version INTEGER NOT NULL DEFAULT 1,

    -- ------------------------------------------------------------------
    -- Human-facing metadata (admin/catalog UI)
    -- ------------------------------------------------------------------
    name VARCHAR(100) NOT NULL,
    description VARCHAR(1000),

    -- ------------------------------------------------------------------
    -- Stable runtime identifier (tenant-scoped)
    -- ------------------------------------------------------------------
    -- Stable key used by systems/integrations. Example: "priority", "customer_email".
    component_key VARCHAR(100) NOT NULL,

    -- UI label shown to end users (optional; some components may render without a label).
    component_label VARCHAR(255),

    -- Optional category used by builder UI to group components in palettes (accordion).
    -- This is a tenant-local classification and does not affect runtime semantics.
    category_id UUID,

    -- ------------------------------------------------------------------
    -- UI and behavior configuration
    -- ------------------------------------------------------------------
    -- Flexible JSONB for UI hints, rendering instructions, and optional runtime behavior.
    -- Examples:
    --   { "placeholder": "Enter value", "help_text": "...", "render_as": "radio" }
    --   { "action_type": "WORKFLOW_TRANSITION", "transition_key": "approve" }
    ui_config JSONB,

    -- ------------------------------------------------------------------
    -- Lifecycle / catalog availability
    -- ------------------------------------------------------------------
    -- Published means "available for use/selection" in the catalog surface.
    -- Default TRUE (most components are usable when created).
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    published_at TIMESTAMPTZ,

    -- Archived means "no longer actively offered" but retained for history/back-compat.
    -- Default should be FALSE for newly created components (fixed from TRUE).
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    archived_at TIMESTAMPTZ,


    source_type dyno_form.artifact_source_type,
    source_package_key VARCHAR(400),
    source_artifact_key VARCHAR(400),
    source_artifact_version VARCHAR(100),
    source_checksum VARCHAR(64),
    installed_at TIMESTAMPTZ,
    installed_by VARCHAR(100),

    -- ------------------------------------------------------------------
    -- Audit columns
    -- ------------------------------------------------------------------
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- ------------------------------------------------------------------
    -- Constraints
    -- ------------------------------------------------------------------

    CONSTRAINT ux_component_id_tenant 
        UNIQUE (tenant_id, id),

    -- Ensure version is sensible.
    CONSTRAINT ck_component_version_positive
        CHECK (component_version >= 1),

    -- Prevent empty/whitespace-only keys (defensive; trims are app-level too).
    CONSTRAINT ck_component_business_key_nonblank
        CHECK (length(btrim(component_business_key)) > 0),

    CONSTRAINT ck_component_key_nonblank
        CHECK (length(btrim(component_key)) > 0),

    CONSTRAINT ck_component_name_nonblank
        CHECK (length(btrim(name)) > 0),

    -- Tenant-safe FK to builder palette category.
    -- Requires a UNIQUE/PK on dyno_form.form_catalog_category(tenant_id, id) or equivalent.
    CONSTRAINT fk_component_category_tenant
        FOREIGN KEY (tenant_id, category_id)
        REFERENCES dyno_form.form_catalog_category (tenant_id, id)
        ON DELETE SET NULL,

    -- Publishing timestamp must align with the published flag.
    CONSTRAINT ck_component_published_at_consistency
        CHECK (
            (is_published = TRUE  AND published_at IS NOT NULL)
         OR (is_published = FALSE AND published_at IS NULL)
        ),

    -- Archiving timestamp must align with the archived flag.
    CONSTRAINT ck_component_archived_at_consistency
        CHECK (
            (is_archived = TRUE  AND archived_at IS NOT NULL)
         OR (is_archived = FALSE AND archived_at IS NULL)
        ),

    -- Versioned catalog identity within tenant.
    CONSTRAINT uq_component_tenant_business_key_version
        UNIQUE (tenant_id, component_business_key, component_version),

    -- Stable runtime identity within tenant.
    CONSTRAINT uq_component_tenant_component_key_version
        UNIQUE (tenant_id, component_key, component_version),


    CONSTRAINT ck_component_source_checksum_format
        CHECK (source_checksum IS NULL OR source_checksum ~ '^[0-9a-f]{64}$')

);

CREATE INDEX IF NOT EXISTS ix_component_tenant_source_type
    ON dyno_form.component (tenant_id, source_type);

CREATE INDEX IF NOT EXISTS ix_component_tenant_source_keys
    ON dyno_form.component (tenant_id, source_package_key, source_artifact_key, source_artifact_version);

-- ----------------------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------------------
-- Primary lookup patterns:
--   - list components for a tenant (optionally only published / not archived)
--   - resolve by component_key (unique) or by (business_key, version)
--   - search/browse by name within tenant
--   - filter by published/archived state within tenant
--   - builder palette filtering by category
-- ----------------------------------------------------------------------

-- Builder palette filtering: list components by tenant and category.
CREATE INDEX IF NOT EXISTS ix_component_tenant_category
    ON dyno_form.component (tenant_id, category_id);

-- Browse/search by name within tenant (supports prefix/ordering use cases).
CREATE INDEX IF NOT EXISTS ix_component_tenant_name
    ON dyno_form.component (tenant_id, name);

-- Supports "catalog" listing filters quickly (tenant + lifecycle flags).
CREATE INDEX IF NOT EXISTS ix_component_tenant_catalog_state
    ON dyno_form.component (tenant_id, is_published, is_archived);

-- Optional: search within category by name in builder UI.
CREATE INDEX IF NOT EXISTS ix_component_tenant_category_name
    ON dyno_form.component (tenant_id, category_id, name)
    WHERE category_id IS NOT NULL;

-- ----------------------------------------------------------------------
-- Column Comments
-- ----------------------------------------------------------------------

COMMENT ON TABLE dyno_form.component IS
'Reusable, tenant-scoped form component. Supports provider/marketplace seeding and tenant-defined components. Includes stable keys, versioning, optional builder category assignment, UI config, publish/archive lifecycle, and audit fields.';

COMMENT ON COLUMN dyno_form.component.id IS
'Primary row identifier (UUID). Immutable technical identity.';

COMMENT ON COLUMN dyno_form.component.tenant_id IS
'Tenant boundary. All component rows are scoped to a tenant for isolation and access control.';

COMMENT ON COLUMN dyno_form.component.component_business_key IS
'Stable catalog/business identifier for the conceptual component. Used with component_version to represent versioned releases of the same component within a tenant (and across tenants via marketplace import).';

COMMENT ON COLUMN dyno_form.component.component_version IS
'Version number for a given (tenant_id, component_business_key). Starts at 1 and increments for new releases.';

COMMENT ON COLUMN dyno_form.component.name IS
'Human-readable name used in admin/catalog UI. Not required to be unique.';

COMMENT ON COLUMN dyno_form.component.description IS
'Optional human-readable description for admin/catalog UI.';

COMMENT ON COLUMN dyno_form.component.component_key IS
'Stable tenant-scoped key used by APIs, automations, and references from other tables. Unique within tenant.';

COMMENT ON COLUMN dyno_form.component.component_label IS
'Human-readable label shown in end-user UI. Optional; some components may not render a label.';

COMMENT ON COLUMN dyno_form.component.category_id IS
'Optional reference to dyno_form.form_catalog_category for grouping components in the builder palette UI (accordion/categories). Tenant-local classification only.';

COMMENT ON COLUMN dyno_form.component.ui_config IS
'JSONB configuration for UI hints and behavior (rendering options, help text, action config, etc.).';

COMMENT ON COLUMN dyno_form.component.is_published IS
'When true, component is available for selection/use in catalog surfaces. When false, it is hidden/unavailable (but may still exist for history).';

COMMENT ON COLUMN dyno_form.component.published_at IS
'Timestamp when the component was published. Must be non-null only when is_published is true.';

COMMENT ON COLUMN dyno_form.component.is_archived IS
'When true, component is archived (retained for history/back-compat but not actively offered).';

COMMENT ON COLUMN dyno_form.component.archived_at IS
'Timestamp when the component was archived. Must be non-null only when is_archived is true.';

COMMENT ON COLUMN dyno_form.component.source_type IS
    'Provenance classification of the artifact installation. Allowed values: MARKETPLACE, PROVIDER, TENANT, SYSTEM.';

COMMENT ON COLUMN dyno_form.component.source_package_key IS
    'Key identifying the package from which this component artifact originated (e.g., marketplace or provider package).';

COMMENT ON COLUMN dyno_form.component.source_artifact_key IS
    'Key identifying the specific artifact within the source package.';

COMMENT ON COLUMN dyno_form.component.source_artifact_version IS
    'Version string of the source artifact from which this component was installed.';

COMMENT ON COLUMN dyno_form.component.source_checksum IS
    'SHA-256 checksum (64 hex characters) of the source artifact at install time. Used to detect source changes and upgrade eligibility.';

COMMENT ON COLUMN dyno_form.component.installed_at IS
    'Timestamp when this component artifact was installed for the tenant.';

COMMENT ON COLUMN dyno_form.component.installed_by IS
    'Actor (username/service) that installed this component artifact.';
    

COMMENT ON COLUMN dyno_form.component.created_at IS
'Row creation timestamp.';

COMMENT ON COLUMN dyno_form.component.updated_at IS
'Row last-updated timestamp. Typically maintained by application code or a trigger.';

COMMENT ON COLUMN dyno_form.component.created_by IS
'Optional actor identifier (username/service) that created the row.';

COMMENT ON COLUMN dyno_form.component.updated_by IS
'Optional actor identifier (username/service) that last updated the row.';



-- ----------------------------------------------------------------------
-- Table: dyno_form.component_panel
-- ----------------------------------------------------------------------
-- PURPOSE
--   Defines a panel within a reusable component.
--   A panel is a logical + visual segment used to group fields and/or nested panels.
--
-- CORE CONCEPTS
--   - Hierarchy:
--       Panels can nest via parent_panel_id, forming a tree under a component.
--       Root panels have parent_panel_id = NULL.
--   - Stable identity:
--       panel_key is a stable, tenant-scoped identifier used by APIs and references.
--       panel_label is a user-facing label shown in UI.
--   - ui_config:
--       JSONB for layout/styling/behavior hints (think "panel container" hints, not business data).
--   - panel_actions:
--       JSONB declarative rules that define reactive behavior between fields, panels,
--       and components contained within this panel.
--
-- IMPORTANT INVARIANTS
--   - tenant_id scopes data to a tenant boundary.
--   - component_id must belong to the same tenant_id (tenant-safe FK).
--   - parent_panel_id (when present) must:
--       * exist
--       * belong to the same tenant_id
--       * belong to the same component_id
--   - panel_key is unique per (tenant_id, component_id).
--   - A panel cannot parent itself.
--   - updated_at is maintained by application code or a DB trigger (not included here).
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_form.component_panel (
    -- ------------------------------------------------------------------
    -- Primary identity
    -- ------------------------------------------------------------------
    id UUID PRIMARY KEY,

    -- ------------------------------------------------------------------
    -- Tenant boundary and owning component
    -- ------------------------------------------------------------------
    tenant_id UUID NOT NULL,

    -- The component this panel belongs to.
    component_id UUID NOT NULL,

    -- Parent component panel (null if root panel).
    parent_panel_id UUID,

    -- Stable key for referencing this panel within the component.
    -- Intended for APIs, templates, and deterministic lookup.
    panel_key VARCHAR(200) NOT NULL,

    -- Human-readable label shown in UI.
    panel_label VARCHAR(200),

    -- Optional JSON UI configuration (layout/styling/behavior hints).
    -- Examples:
    --   { "layout": "two_column", "css": {"gap": "12px"}, "collapsible": true }
    ui_config JSONB,

    -- ------------------------------------------------------------------
    -- Panel interaction rules
    -- ------------------------------------------------------------------
    -- Declarative JSON rules that define reactive behavior between fields,
    -- panels, and components contained within this panel.
    --
    -- Intended use cases:
    --   - Toggle visibility or enabled/required state of fields or panels
    --     based on changes in other fields (e.g. checkbox on/off).
    --   - Switch between mutually exclusive panels or component variants
    --     based on selected option values.
    --   - Coordinate simple UI state changes without embedding executable code.
    --
    -- Expected characteristics:
    --   - Declarative (no scripts or expressions).
    --   - References targets and sources by stable keys (panel_key, field_key,
    --     component_key), never labels.
    --   - Schema-validated and interpreted by application/UI logic.
    panel_actions JSONB,

    -- ------------------------------------------------------------------
    -- Audit columns
    -- ------------------------------------------------------------------
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- ------------------------------------------------------------------
    -- Constraints
    -- ------------------------------------------------------------------

    -- Ensure tenant‑safe unique constraints
    CONSTRAINT ux_component_panel_id_tenant 
        UNIQUE (tenant_id, id),

    -- unique constraint for parent panels to support FK fk_component_panel_parent_panel_tenant_component
    CONSTRAINT ux_component_panel_tenant_component_id 
        UNIQUE (tenant_id, component_id, id),

    -- Enforce hierarchical integrity for component panels.
    --
    -- This self-referencing foreign key guarantees that when a panel declares a
    -- parent_panel_id, that parent:
    --   1) EXISTS (referential integrity)
    --   2) Belongs to the SAME tenant (tenant_id match)
    --   3) Belongs to the SAME component (component_id match)
    --
    -- Why component_id is intentionally included:
    --   Panels form a tree that is strictly scoped to a single component.
    --   A panel must NEVER be allowed to parent a panel from a different component,
    --   even if they belong to the same tenant.
    --
    -- Using a simplified FK on (tenant_id, parent_panel_id) would be insufficient,
    -- because it would allow cross-component parenting within the same tenant.
    -- That would violate the core domain invariant and could corrupt the panel tree.
    --
    -- Performance tradeoff:
    --   This table is not write-heavy, and panel hierarchy changes are relatively rare
    --   compared to read operations. The additional column in the FK and supporting
    --   index has negligible impact on performance, while providing strong correctness
    --   guarantees enforced directly by the database.
    --
    -- ON DELETE CASCADE is intentional:
    --   Deleting a parent panel deletes its entire subtree, which matches the
    --   ownership semantics of component panels.
    --
    -- Correctness and invariant enforcement are prioritized over marginal FK
    -- simplification or micro-optimizations.
    CONSTRAINT fk_component_panel_parent_panel_tenant_component 
        FOREIGN KEY (tenant_id, component_id, parent_panel_id)
        REFERENCES dyno_form.component_panel (tenant_id, component_id, id)
        ON DELETE CASCADE,

    -- Defensive: prevent empty/whitespace-only keys.
    CONSTRAINT ck_component_panel_key_nonblank
        CHECK (length(btrim(panel_key)) > 0),

    -- Defensive: prevent empty/whitespace-only label if provided.
    CONSTRAINT ck_component_panel_label_nonblank
        CHECK (panel_label IS NULL OR length(btrim(panel_label)) > 0),

    -- Prevent self-parenting.
    CONSTRAINT ck_component_panel_no_self_parent
        CHECK (parent_panel_id IS NULL OR parent_panel_id <> id),

    -- Stable identity within a component.
    CONSTRAINT uq_component_panel_tenant_component_panel_key
        UNIQUE (tenant_id, component_id, panel_key),

    -- ------------------------------------------------------------------
    -- Foreign keys (tenant-safe)
    -- ------------------------------------------------------------------

    -- Tenant-safe FK: forces component_id to belong to same tenant_id.
    -- Requires a UNIQUE/PK on dyno_form.component(tenant_id, id) or equivalent.
    CONSTRAINT fk_component_panel_component_tenant
        FOREIGN KEY (tenant_id, component_id)
        REFERENCES dyno_form.component (tenant_id, id)
        ON DELETE CASCADE,
);

-- ----------------------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------------------
-- Common access patterns:
--   - list panels for a component (and build a tree)
--   - fetch children for a given parent_panel_id
--   - resolve by (tenant_id, component_id, panel_key)
-- ----------------------------------------------------------------------

-- Fetch children by parent quickly (tree traversal).
CREATE INDEX IF NOT EXISTS ix_component_panel_parent
    ON dyno_form.component_panel (tenant_id, component_id, parent_panel_id);


-- Optional but useful when ordering/recency queries exist.
CREATE INDEX IF NOT EXISTS ix_component_panel_tenant_component_updated_at
    ON dyno_form.component_panel (tenant_id, component_id, updated_at);

-- ----------------------------------------------------------------------
-- Comments
-- ----------------------------------------------------------------------

COMMENT ON TABLE dyno_form.component_panel IS
'Panel within a reusable component. Panels are hierarchical (parent_panel_id) and group fields or nested panels. Includes declarative panel-level interaction rules via panel_actions. Tenant-scoped and component-scoped with tenant-safe foreign keys.';

COMMENT ON COLUMN dyno_form.component_panel.id IS
'Primary row identifier (UUID). Immutable technical identity.';

COMMENT ON COLUMN dyno_form.component_panel.tenant_id IS
'Tenant boundary. All panel rows are scoped to a tenant for isolation and access control.';

COMMENT ON COLUMN dyno_form.component_panel.component_id IS
'Owning component ID. Panel belongs to exactly one component.';

COMMENT ON COLUMN dyno_form.component_panel.parent_panel_id IS
'Optional parent panel ID for nesting. NULL indicates a root panel within the component. Parent must be in the same tenant and component.';

COMMENT ON COLUMN dyno_form.component_panel.panel_key IS
'Stable identifier for this panel within (tenant_id, component_id). Used by APIs/templates and for deterministic lookup.';

COMMENT ON COLUMN dyno_form.component_panel.panel_label IS
'Human-readable label shown in UI. Optional.';

COMMENT ON COLUMN dyno_form.component_panel.ui_config IS
'JSONB UI configuration for layout, styling, and container-level rendering hints.';

COMMENT ON COLUMN dyno_form.component_panel.panel_actions IS
'JSONB declarative interaction rules that define how fields, panels, and component variants within this panel react to user input and state changes.';

COMMENT ON COLUMN dyno_form.component_panel.created_at IS
'Row creation timestamp.';

COMMENT ON COLUMN dyno_form.component_panel.updated_at IS
'Row last-updated timestamp. Typically maintained by application code or a trigger.';

COMMENT ON COLUMN dyno_form.component_panel.created_by IS
'Optional actor identifier (username/service) that created the row.';

COMMENT ON COLUMN dyno_form.component_panel.updated_by IS
'Optional actor identifier (username/service) that last updated the row.';


-- ----------------------------------------------------------------------
-- Table: dyno_form.component_panel_field
-- ----------------------------------------------------------------------
-- PURPOSE
--   Defines the placement of a reusable field definition (field_def) onto a
--   specific component panel. This table is the "composition" layer that:
--     - attaches a field_def to a panel (provenance / reset source)
--     - defines the display order of the field within that panel
--     - allows per-panel overrides of the field_def UI configuration
--     - stores an imprinted, editable field configuration snapshot (field_config)
--
-- CORE CONCEPTS
--   - Composition (panel + field_def):
--       A panel contains zero or more fields. Each row represents one field instance
--       placed on that panel, backed by a reusable field_def.
--   - Ordering:
--       field_order controls default tab / display ordering within the panel.
--       Ordering is panel-scoped (not global).
--   - UI configuration overrides:
--       field_def.ui_config is the base configuration.
--       component_panel_field.ui_config is an override/augmentation applied in the
--       context of this specific panel placement.
--   - Imprinting (field_config):
--       field_config is a JSONB snapshot that can fully represent the effective
--       field_def and its options at the time the field was placed.
--       Edits to the placed field update field_config, leaving field_def unchanged.
--       A reset action can re-imprint field_config from the referenced field_def.
--   - Hashing:
--       * field_config_hash: hash of the current field_config JSONB (detect edits/diff).
--       * source_field_def_hash: hash of the canonical source snapshot from field_def
--         (field_def + field_def_option) at the time of imprint (detect catalog drift).
--
-- IMPORTANT INVARIANTS
--   - tenant_id scopes data to a tenant boundary.
--   - panel_id must belong to the same tenant_id (tenant-safe FK).
--   - field_def_id must belong to the same tenant_id (tenant-safe FK).
--   - A given (tenant_id, panel_id, field_def_id) should be unique to prevent
--     accidental duplicate placement of the same field_def on the same panel.
--   - field_order, when provided, must be >= 0.
--   - field_config must conform to the JSON schema enforced by jsonb_matches_schema.
--   - Hash columns are typically maintained by application logic or triggers.
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_form.component_panel_field (
    -- ------------------------------------------------------------------
    -- Primary identity
    -- ------------------------------------------------------------------
    id UUID PRIMARY KEY,

    -- ------------------------------------------------------------------
    -- Tenant boundary and owning panel
    -- ------------------------------------------------------------------
    tenant_id UUID NOT NULL,

    -- The component panel this field belongs to.
    panel_id UUID NOT NULL,

    -- The field definition used as the source for this field placement.
    -- This is provenance and reset source. The placed field's effective definition
    -- lives in field_config (imprinted snapshot).
    field_def_id UUID NOT NULL,

    -- Default display/tab order within the panel.
    -- Null means "unspecified" (UI/service may apply a default ordering strategy).
    field_order INTEGER,

    -- field_def has its own ui_config; ui_config here are overrides for this placement.
    ui_config JSONB,

    -- ------------------------------------------------------------------
    -- Imprinted field definition snapshot
    -- ------------------------------------------------------------------
    -- JSONB snapshot representing the effective field definition and options for this
    -- placement. This is the editable copy that can diverge from the catalog field_def.
    --
    -- The schema is enforced via public.jsonb_matches_schema(field_config, <schema>).
    field_config JSONB NOT NULL,

    -- Hash of the current field_config JSONB (typically sha256 hex, 64 chars).
    -- Used to detect edits and support fast diff checks without deep JSON comparison.
    field_config_hash VARCHAR(64),

    -- Hash of the canonical source snapshot from field_def + field_def_option that was
    -- used to imprint field_config initially (typically sha256 hex, 64 chars).
    -- Used to detect when the catalog source changed since imprint (reset candidate).
    source_field_def_hash VARCHAR(64),

    -- Timestamp when field_config was last imprinted from the catalog source.
    last_imprinted_at TIMESTAMPTZ,

    -- ------------------------------------------------------------------
    -- Audit columns
    -- ------------------------------------------------------------------
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- ------------------------------------------------------------------
    -- Constraints
    -- ------------------------------------------------------------------

    -- Ensure tenant‑safe unique constraints
    CONSTRAINT ux_component_panel_field_tenant_id
        UNIQUE (tenant_id, id),

    -- Defensive: ordering, when provided, must be non-negative.
    CONSTRAINT ck_component_panel_field_order_non_negative
        CHECK (field_order IS NULL OR field_order >= 0),

    -- Prevent duplicate placement of the same field_def on the same panel.
    CONSTRAINT uq_component_panel_field_panel_field_def
        UNIQUE (tenant_id, panel_id, field_def_id),

    -- Optional: enforce a single field_order value per panel when field_order is used.
    -- This helps prevent "two fields share order 10" ambiguity.
    -- (Allows multiple NULLs.)
    CONSTRAINT uq_component_panel_field_panel_order
        UNIQUE (tenant_id, panel_id, field_order),

    -- Enforce hash formatting when provided (sha256 hex).
    CONSTRAINT ck_component_panel_field_field_config_hash_format
        CHECK (field_config_hash IS NULL OR field_config_hash ~ '^[0-9a-f]{64}$'),

    CONSTRAINT ck_component_panel_field_source_field_def_hash_format
        CHECK (source_field_def_hash IS NULL OR source_field_def_hash ~ '^[0-9a-f]{64}$'),

    -- Enforce field_config JSON schema.
    -- NOTE: This assumes public.jsonb_matches_schema(instance_jsonb, schema_jsonb) exists.
    CONSTRAINT ck_component_panel_field_field_config_schema
        CHECK (
            public.jsonb_matches_schema(
                field_config,
                $${
                  "$schema": "http://json-schema.org/draft-07/schema#",
                  "title": "DynoCRM Component Panel Field Config",
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["schema_version", "field"],
                  "properties": {
                    "schema_version": { "type": "integer", "minimum": 1 },

                    "field": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": ["field_key", "label", "element_type"],
                      "properties": {
                        "field_def_business_key": { "type": "string", "minLength": 1, "maxLength": 400 },
                        "field_def_version": { "type": "integer", "minimum": 1 },

                        "name": { "type": "string", "minLength": 1, "maxLength": 100 },
                        "description": { "type": ["string", "null"], "maxLength": 1000 },

                        "field_key": { "type": "string", "minLength": 1, "maxLength": 100 },
                        "label": { "type": "string", "minLength": 1, "maxLength": 255 },

                        "category_id": { "type": ["string", "null"], "pattern": "^[0-9a-fA-F-]{36}$" },

                        "data_type": {
                          "type": ["string", "null"],
                          "enum": ["TEXT","NUMBER","BOOLEAN","DATE","DATETIME","SINGLESELECT","MULTISELECT", null]
                        },

                        "element_type": {
                          "type": "string",
                          "enum": ["TEXT","TEXTAREA","DATE","DATETIME","SELECT","MULTISELECT","ACTION"]
                        },

                        "validation": { "type": ["object", "null"] },
                        "ui_config": { "type": ["object", "null"] }
                      }
                    },

                    "options": {
                      "type": ["array", "null"],
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": ["option_key", "option_label", "option_order"],
                        "properties": {
                          "option_key": { "type": "string", "minLength": 1, "maxLength": 200 },
                          "option_label": { "type": "string", "minLength": 1, "maxLength": 400 },
                          "option_order": { "type": "integer", "minimum": 0 }
                        }
                      }
                    }
                  }
                }$$::jsonb
            )
        ),

    -- ------------------------------------------------------------------
    -- Foreign keys (tenant-safe)
    -- ------------------------------------------------------------------

    -- Tenant-safe: forces panel_id to belong to same tenant_id.
    -- Requires a UNIQUE/PK on dyno_form.component_panel(tenant_id, id) or equivalent.
    CONSTRAINT fk_component_panel_field_panel_tenant
        FOREIGN KEY (tenant_id, panel_id)
        REFERENCES dyno_form.component_panel (tenant_id, id)
        ON DELETE CASCADE,

    CONSTRAINT fk_component_panel_field_field_def_tenant
        FOREIGN KEY (tenant_id, field_def_id)
        REFERENCES dyno_form.field_def (tenant_id, id)
        ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------------------
-- Common access patterns:
--   - list all fields for a panel ordered by field_order
--   - join to field_def to render the panel
--   - tenant-scoped maintenance queries
--   - diff/reset workflows (hash comparisons)
-- ----------------------------------------------------------------------

-- Fast joins to field_def (when rendering / reset provenance).
CREATE INDEX IF NOT EXISTS ix_component_panel_field_field_def
    ON dyno_form.component_panel_field (tenant_id, field_def_id);

-- Optional: JSONB search/filtering on ui_config traits.
CREATE INDEX IF NOT EXISTS ix_component_panel_field_ui_config_gin
    ON dyno_form.component_panel_field
    USING GIN (ui_config);

-- Optional: JSONB search/filtering on field_config traits (debugging, analysis, admin tools).
CREATE INDEX IF NOT EXISTS ix_component_panel_field_field_config_gin
    ON dyno_form.component_panel_field
    USING GIN (field_config);

-- Optional: useful for recency queries and debugging.
CREATE INDEX IF NOT EXISTS ix_component_panel_field_tenant_panel_updated_at
    ON dyno_form.component_panel_field (tenant_id, panel_id, updated_at);

-- Optional: accelerate "is overridden" checks via hash comparisons.
CREATE INDEX IF NOT EXISTS ix_component_panel_field_hashes
    ON dyno_form.component_panel_field (tenant_id, field_config_hash, source_field_def_hash);

-- ----------------------------------------------------------------------
-- Comments
-- ----------------------------------------------------------------------

COMMENT ON TABLE dyno_form.component_panel_field IS
'Places a reusable field_def onto a specific component panel. Controls per-panel ordering and supports per-placement UI configuration overrides. Stores an imprinted, editable field_config snapshot (field_def + options) with schema enforcement and hashes for diff/reset workflows.';

COMMENT ON COLUMN dyno_form.component_panel_field.id IS
'Primary row identifier (UUID). Immutable technical identity.';

COMMENT ON COLUMN dyno_form.component_panel_field.tenant_id IS
'Tenant boundary. All rows are scoped to a tenant for isolation and access control.';

COMMENT ON COLUMN dyno_form.component_panel_field.panel_id IS
'Owning component panel ID. The panel that this field placement belongs to.';

COMMENT ON COLUMN dyno_form.component_panel_field.field_def_id IS
'Source catalog field definition ID (field_def). Used for provenance and reset/re-imprint. The effective field definition for this placement lives in field_config.';

COMMENT ON COLUMN dyno_form.component_panel_field.field_order IS
'Default display/tab order within the panel. Null means unspecified; otherwise non-negative and unique within (tenant_id, panel_id) when present.';

COMMENT ON COLUMN dyno_form.component_panel_field.ui_config IS
'JSONB UI configuration overrides applied on top of the field_config.ui_config for this specific panel placement (layout/display hints).';

COMMENT ON COLUMN dyno_form.component_panel_field.field_config IS
'Imprinted JSONB snapshot of the effective field definition for this placement, including option definitions for select/multiselect. Editable without mutating the source field_def. Enforced by jsonb_matches_schema.';

COMMENT ON COLUMN dyno_form.component_panel_field.field_config_hash IS
'Hash (typically sha256 hex) of the current field_config JSONB. Used to detect edits and support diff workflows efficiently.';

COMMENT ON COLUMN dyno_form.component_panel_field.source_field_def_hash IS
'Hash (typically sha256 hex) of the canonical source snapshot from field_def + field_def_option at the time field_config was last imprinted. Used to detect catalog drift since imprint.';

COMMENT ON COLUMN dyno_form.component_panel_field.last_imprinted_at IS
'Timestamp of the last imprint operation that copied the catalog source definition into field_config.';

COMMENT ON COLUMN dyno_form.component_panel_field.created_at IS
'Row creation timestamp.';

COMMENT ON COLUMN dyno_form.component_panel_field.updated_at IS
'Row last-updated timestamp. Typically maintained by application code or a trigger.';

COMMENT ON COLUMN dyno_form.component_panel_field.created_by IS
'Optional actor identifier (username/service) that created the row.';

COMMENT ON COLUMN dyno_form.component_panel_field.updated_by IS
'Optional actor identifier (username/service) that last updated the row.';



-- 



-- ----------------------------------------------------------------------
-- Table: dyno_form.form
-- ----------------------------------------------------------------------
-- PURPOSE
--   Defines an actual form definition for a tenant.
--
--   A form is not a reusable catalog component. It is the concrete form
--   definition that will be used for submissions. Forms can embed reusable
--   catalog components and can also include direct form fields, but this table
--   is the root identity and lifecycle container for the form definition.
--
-- CORE CONCEPTS
--   - Business identity vs row identity:
--       * id is the immutable row identifier (UUID PK).
--       * form_business_key + form_version provides a stable versioned identity
--         for the conceptual form across publish cycles.
--   - Human-facing metadata:
--       * name and description support builder UI listing and management.
--   - Lifecycle:
--       * is_published controls availability for use in submissions.
--       * is_archived indicates the form is no longer actively offered but is
--         retained for history/back-compat.
--
-- IMPORTANT INVARIANTS
--   - tenant_id scopes all data to a tenant boundary.
--   - form_business_key + form_version is unique per tenant.
--   - Publishing / archiving timestamps are consistent with their flags:
--       * is_published = true  => published_at is not null
--       * is_published = false => published_at is null
--       * is_archived = true   => archived_at is not null
--       * is_archived = false  => archived_at is null
--   - updated_at is maintained by application code or a DB trigger (not included here).
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_form.form (
    -- ------------------------------------------------------------------
    -- Primary identity
    -- ------------------------------------------------------------------
    id UUID PRIMARY KEY,

    -- Tenant boundary. This table is always tenant-scoped.
    tenant_id UUID NOT NULL,

    -- ------------------------------------------------------------------
    -- Versioned business identity
    -- ------------------------------------------------------------------
    -- Stable business key used to identify a form across versions within a tenant.
    -- Typically used for import/export and version lineage.
    form_business_key VARCHAR(400) NOT NULL,

    -- Monotonic version number for a given (tenant_id, form_business_key).
    -- Typically starts at 1 and increments for new versions.
    form_version INTEGER NOT NULL DEFAULT 1,

    -- ------------------------------------------------------------------
    -- Human-facing metadata (builder/admin UI)
    -- ------------------------------------------------------------------
    name VARCHAR(255) NOT NULL,
    description VARCHAR(500),

    -- ------------------------------------------------------------------
    -- Lifecycle / availability
    -- ------------------------------------------------------------------
    -- Published means "available to be used for new submissions".
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    published_at TIMESTAMPTZ,

    -- Archived means "retained for history/back-compat but not actively offered".
    -- Default should be FALSE for newly created forms.
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    archived_at TIMESTAMPTZ,


    source_type dyno_form.artifact_source_type,
    source_package_key VARCHAR(400),
    source_artifact_key VARCHAR(400),
    source_artifact_version VARCHAR(100),
    source_checksum VARCHAR(64),
    installed_at TIMESTAMPTZ,
    installed_by VARCHAR(100),

    -- ------------------------------------------------------------------
    -- Audit columns
    -- ------------------------------------------------------------------
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- ------------------------------------------------------------------
    -- Constraints
    -- ------------------------------------------------------------------

    -- Supports tenant-safe composite foreign keys from child tables.
    CONSTRAINT ux_form_id_tenant 
        UNIQUE (tenant_id, id),

    -- Ensure version is sensible.
    CONSTRAINT ck_form_version_positive
        CHECK (form_version >= 1),

    -- Prevent blank/whitespace identifiers.
    CONSTRAINT ck_form_business_key_nonblank
        CHECK (length(btrim(form_business_key)) > 0),

    CONSTRAINT ck_form_name_nonblank
        CHECK (length(btrim(name)) > 0),

    -- Versioned identity uniqueness within tenant.
    CONSTRAINT uq_form_tenant_business_key_version
        UNIQUE (tenant_id, form_business_key, form_version),

    -- Publishing timestamp must align with published flag.
    CONSTRAINT ck_form_published_at_consistency
        CHECK (
            (is_published = TRUE  AND published_at IS NOT NULL)
         OR (is_published = FALSE AND published_at IS NULL)
        ),

    -- Archiving timestamp must align with archived flag.
    CONSTRAINT ck_form_archived_at_consistency
        CHECK (
            (is_archived = TRUE  AND archived_at IS NOT NULL)
         OR (is_archived = FALSE AND archived_at IS NULL)
        ),

    CONSTRAINT ck_form_source_checksum_format
        CHECK (source_checksum IS NULL OR source_checksum ~ '^[0-9a-f]{64}$')
);

-- ----------------------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------------------
-- Common access patterns:
--   - list forms by tenant (optionally only published / not archived)
--   - resolve by (business_key, version) or get latest version
--   - search/browse by name within tenant
-- ----------------------------------------------------------------------

-- Uniqueness: one name per tenant (builder UI friendly).
CREATE UNIQUE INDEX IF NOT EXISTS ux_form_tenant_name
    ON dyno_form.form (tenant_id, name);

-- Catalog listing filters (published / archived).
CREATE INDEX IF NOT EXISTS ix_form_tenant_catalog_state
    ON dyno_form.form (tenant_id, is_published, is_archived);

-- Optional: case-insensitive search by name.
CREATE INDEX IF NOT EXISTS ix_form_tenant_name_lower
    ON dyno_form.form (tenant_id, lower(name));

CREATE INDEX IF NOT EXISTS ix_form_tenant_source_type
    ON dyno_form.form (tenant_id, source_type);

CREATE INDEX IF NOT EXISTS ix_form_tenant_source_keys
    ON dyno_form.form (tenant_id, source_package_key, source_artifact_key, source_artifact_version);

-- ----------------------------------------------------------------------
-- Comments
-- ----------------------------------------------------------------------

COMMENT ON TABLE dyno_form.form IS
'Actual tenant-scoped form definition (non-reusable). Uses a versioned business identity (form_business_key + form_version) and lifecycle flags to control availability for new submissions while retaining older versions for history/back-compat.';

COMMENT ON COLUMN dyno_form.form.id IS
'Primary row identifier (UUID). Immutable technical identity.';

COMMENT ON COLUMN dyno_form.form.tenant_id IS
'Tenant boundary. All form rows are scoped to a tenant for isolation and access control.';

COMMENT ON COLUMN dyno_form.form.form_business_key IS
'Stable business identifier for the conceptual form across versions within a tenant. Used for version lineage and import/export.';

COMMENT ON COLUMN dyno_form.form.form_version IS
'Version number for a given (tenant_id, form_business_key). Starts at 1 and increments for new versions.';

COMMENT ON COLUMN dyno_form.form.name IS
'Human-readable name shown in builder/admin UI. Unique within a tenant.';

COMMENT ON COLUMN dyno_form.form.description IS
'Optional human-readable description for builder/admin UI.';

COMMENT ON COLUMN dyno_form.form.is_published IS
'When true, the form is available for selection and new submissions. When false, it is hidden/unavailable for new use.';

COMMENT ON COLUMN dyno_form.form.published_at IS
'Timestamp when the form was published. Must be non-null only when is_published is true.';

COMMENT ON COLUMN dyno_form.form.is_archived IS
'When true, the form is archived (retained for history/back-compat but not actively offered).';

COMMENT ON COLUMN dyno_form.form.archived_at IS
'Timestamp when the form was archived. Must be non-null only when is_archived is true.';

COMMENT ON COLUMN dyno_form.form.source_type IS
    'Provenance classification of the artifact installation. Allowed values: MARKETPLACE, PROVIDER, TENANT, SYSTEM.';

COMMENT ON COLUMN dyno_form.form.source_package_key IS
    'Key identifying the package from which this form artifact originated (e.g., marketplace or provider package).';

COMMENT ON COLUMN dyno_form.form.source_artifact_key IS
    'Key identifying the specific artifact within the source package.';

COMMENT ON COLUMN dyno_form.form.source_artifact_version IS
    'Version string of the source artifact from which this form was installed.';

COMMENT ON COLUMN dyno_form.form.source_checksum IS
    'SHA-256 checksum (64 hex characters) of the source artifact at install time. Used to detect source changes and upgrade eligibility.';

COMMENT ON COLUMN dyno_form.form.installed_at IS
    'Timestamp when this form artifact was installed for the tenant.';

COMMENT ON COLUMN dyno_form.form.installed_by IS
    'Actor (username/service) that installed this form artifact.';

COMMENT ON COLUMN dyno_form.form.created_at IS
'Row creation timestamp.';

COMMENT ON COLUMN dyno_form.form.updated_at IS
'Row last-updated timestamp. Typically maintained by application code or a trigger.';

COMMENT ON COLUMN dyno_form.form.created_by IS
'Optional actor identifier (username/service) that created the row.';

COMMENT ON COLUMN dyno_form.form.updated_by IS
'Optional actor identifier (username/service) that last updated the row.';



-- ----------------------------------------------------------------------
-- Table: dyno_form.form_panel
-- ----------------------------------------------------------------------
-- PURPOSE
--   Defines a panel within an actual form definition.
--
--   form_panel is intentionally very similar to component_panel, but it exists
--   in the "form composition" domain (non-reusable instance definition) and it
--   is the primary location where embedded components can be customized without
--   modifying the underlying catalog tables:
--     - dyno_form.component
--     - dyno_form.component_panel
--     - dyno_form.component_panel_field
--
--   The customization mechanism is nested_overrides, which applies PATCH-style
--   overrides to nested panel_config and field_config inside embedded components.
--   This allows a form to tailor a reused component (labels, validation, options,
--   ui hints, panel_actions, etc.) while keeping the catalog component intact.
--
-- CORE CONCEPTS
--   - Stable identity:
--       panel_key is a stable, form-scoped identifier used by builders and APIs.
--       panel_label is the user-facing label shown in UI.
--   - Layout configuration:
--       ui_config contains layout and rendering hints for the panel container.
--   - Embedded component customization:
--       nested_overrides contains selector-addressed patches that apply to:
--         * field_config of component_panel_field nodes
--         * panel_config of component_panel nodes
--       Overrides are always PATCH semantics (no REPLACE mode).
--
-- IMPORTANT INVARIANTS
--   - tenant_id scopes data to a tenant boundary.
--   - form_id must belong to the same tenant_id (tenant-safe FK).
--   - panel_key is unique per (tenant_id, form_id).
--   - nested_overrides must conform to the Nested Overrides JSON schema.
--   - updated_at is maintained by application code or a DB trigger (not included here).
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_form.form_panel (
    -- ------------------------------------------------------------------
    -- Primary identity
    -- ------------------------------------------------------------------
    id UUID PRIMARY KEY,

    -- ------------------------------------------------------------------
    -- Tenant boundary and owning form
    -- ------------------------------------------------------------------
    tenant_id UUID NOT NULL,

    -- The form this panel belongs to.
    form_id UUID NOT NULL,

    -- Stable key for referencing this panel within the form.
    -- Intended for APIs, builders, and deterministic lookup.
    panel_key VARCHAR(200) NOT NULL,

    -- Human-readable label shown in UI.
    panel_label VARCHAR(200),

    -- Optional JSON UI configuration (layout/styling/container hints).
    -- Examples:
    --   { "layout": "two_column", "css": {"gap": "12px"}, "collapsible": true }
    ui_config JSONB,

    -- ------------------------------------------------------------------
    -- Nested override patches for embedded component customization
    -- ------------------------------------------------------------------
    -- JSON document containing selector-addressed PATCH overrides that apply to
    -- nested catalog objects inside components embedded within this form panel.
    --
    -- Why this exists:
    --   Components and their panels/fields are catalog items reused across forms.
    --   A specific form embedding a component often needs small overrides without
    --   forking or mutating the catalog definitions.
    --
    -- How it works:
    --   - The form builder materializes the embedded component tree.
    --   - For each override entry, selector resolves a target node in that tree.
    --   - The provided field_config and/or panel_config objects are merged (PATCH)
    --     into the target node's effective config.
    --
    -- Selector addressing:
    --   - Dot-separated path.
    --   - If selector starts with '.', it is relative to the current embedded component
    --     context within this form_panel.
    --   - If selector does not start with '.', it is absolute from the form root.
    --
    -- Patch semantics:
    --   - Always PATCH (object merge).
    --   - Arrays (such as options lists) are treated as replace-the-array unless a
    --     more advanced id-based merge protocol is introduced later.
    nested_overrides JSONB,

    -- ------------------------------------------------------------------
    -- Audit columns
    -- ------------------------------------------------------------------
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- ------------------------------------------------------------------
    -- Constraints
    -- ------------------------------------------------------------------

    -- Supports tenant-safe composite foreign keys from child tables.
    CONSTRAINT ux_form_panel_tenant_id
        UNIQUE (tenant_id, id),

    -- Defensive: prevent empty/whitespace-only keys.
    CONSTRAINT ck_form_panel_key_nonblank
        CHECK (length(btrim(panel_key)) > 0),

    -- Defensive: prevent empty/whitespace-only label if provided.
    CONSTRAINT ck_form_panel_label_nonblank
        CHECK (panel_label IS NULL OR length(btrim(panel_label)) > 0),

    -- Stable identity within a form.
    CONSTRAINT uq_form_panel_tenant_form_panel_key
        UNIQUE (tenant_id, form_id, panel_key),

    -- Enforce nested_overrides JSON schema when present.
    -- NOTE: Assumes public.jsonb_matches_schema(instance_jsonb, schema_jsonb) exists.
    CONSTRAINT ck_form_panel_nested_overrides_schema
        CHECK (
            nested_overrides IS NULL
            OR public.jsonb_matches_schema(
                nested_overrides,
                $${
                  "$schema": "http://json-schema.org/draft-07/schema#",
                  "title": "DynoCRM Nested Overrides",
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["schema_version", "overrides"],
                  "properties": {
                    "schema_version": { "type": "integer", "minimum": 1 },
                    "overrides": {
                      "type": "array",
                      "items": { "$ref": "#/definitions/override_entry" }
                    }
                  },
                  "definitions": {
                    "override_entry": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": ["selector"],
                      "properties": {
                        "selector": {
                          "type": "string",
                          "minLength": 2,
                          "maxLength": 800,
                          "description": "Dot-separated path. If it starts with '.', it is relative to the current embedded component context; otherwise absolute from the form root.",
                          "pattern": "^(\\.|[A-Za-z0-9_\\-]+)(\\.[A-Za-z0-9_\\-]+)+$"
                        },
                        "field_config": { "$ref": "#/definitions/field_config_patch" },
                        "panel_config": { "$ref": "#/definitions/panel_config_patch" }
                      },
                      "anyOf": [
                        { "required": ["field_config"] },
                        { "required": ["panel_config"] }
                      ]
                    },
                    "field_config_patch": {
                      "type": "object",
                      "additionalProperties": false,
                      "properties": {
                        "field": { "$ref": "#/definitions/field_patch" },
                        "options": { "$ref": "#/definitions/options_patch" }
                      },
                      "minProperties": 1,
                      "description": "PATCH object merged into the target field_config."
                    },
                    "field_patch": {
                      "type": "object",
                      "additionalProperties": true,
                      "description": "Partial patch of the field definition portion. Permissive for forward compatibility.",
                      "properties": {
                        "field_def_business_key": { "type": "string", "minLength": 1, "maxLength": 400 },
                        "field_def_version": { "type": "integer", "minimum": 1 },
                        "name": { "type": "string", "minLength": 1, "maxLength": 100 },
                        "description": { "type": ["string", "null"], "maxLength": 1000 },
                        "field_key": { "type": "string", "minLength": 1, "maxLength": 100 },
                        "label": { "type": "string", "minLength": 1, "maxLength": 255 },
                        "category_id": { "type": ["string", "null"], "pattern": "^[0-9a-fA-F-]{36}$" },
                        "data_type": {
                          "type": ["string", "null"],
                          "enum": ["TEXT","NUMBER","BOOLEAN","DATE","DATETIME","SINGLESELECT","MULTISELECT", null]
                        },
                        "element_type": {
                          "type": "string",
                          "enum": ["TEXT","TEXTAREA","DATE","DATETIME","SELECT","MULTISELECT","ACTION"]
                        },
                        "validation": { "type": ["object", "null"] },
                        "ui_config": { "type": ["object", "null"] }
                      }
                    },
                    "options_patch": {
                      "type": "array",
                      "description": "Full replacement of the option list within the field_config (still PATCH semantics at the override entry level).",
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": ["option_key", "option_label", "option_order"],
                        "properties": {
                          "option_key": { "type": "string", "minLength": 1, "maxLength": 200 },
                          "option_label": { "type": "string", "minLength": 1, "maxLength": 400 },
                          "option_order": { "type": "integer", "minimum": 0 }
                        }
                      }
                    },
                    "panel_config_patch": {
                      "type": "object",
                      "additionalProperties": false,
                      "properties": {
                        "panel_label": { "type": ["string", "null"], "maxLength": 200 },
                        "ui_config": { "type": ["object", "null"] },
                        "panel_actions": { "type": ["object", "null"] }
                      },
                      "minProperties": 1,
                      "description": "PATCH object merged into the target panel config."
                    }
                  }
                }$$::jsonb
            )
        ),

    -- ------------------------------------------------------------------
    -- Foreign keys (tenant-safe)
    -- ------------------------------------------------------------------

    -- Tenant-safe FK: forces form_id to belong to same tenant_id.
    -- Requires a UNIQUE/PK on dyno_form.form(tenant_id, id) or equivalent.
    CONSTRAINT fk_form_panel_form_tenant
        FOREIGN KEY (tenant_id, form_id)
        REFERENCES dyno_form.form (tenant_id, id)
        ON DELETE CASCADE
);

-- ----------------------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------------------
-- Common access patterns:
--   - list panels for a form
--   - resolve a panel by (tenant_id, form_id, panel_key)
--   - search/filter on ui_config or nested_overrides traits (admin/debug tooling)
-- ----------------------------------------------------------------------

-- Load all panels for a form efficiently.
CREATE INDEX IF NOT EXISTS ix_form_panel_tenant_form
    ON dyno_form.form_panel (tenant_id, form_id);

-- Optional: JSONB GIN for searching/filtering on ui_config traits.
CREATE INDEX IF NOT EXISTS ix_form_panel_ui_config_gin
    ON dyno_form.form_panel
    USING GIN (ui_config);

-- Optional: JSONB GIN for searching/filtering on nested_overrides traits.
-- Useful for admin/debugging queries (e.g., "find forms overriding field X").
CREATE INDEX IF NOT EXISTS ix_form_panel_nested_overrides_gin
    ON dyno_form.form_panel
    USING GIN (nested_overrides);

-- Optional: useful for recency queries and debugging.
CREATE INDEX IF NOT EXISTS ix_form_panel_tenant_form_updated_at
    ON dyno_form.form_panel (tenant_id, form_id, updated_at);

-- ----------------------------------------------------------------------
-- Comments
-- ----------------------------------------------------------------------

COMMENT ON TABLE dyno_form.form_panel IS
'Panel within an actual form definition. Similar to component_panel but used for form composition. Supports nested_overrides to PATCH embedded catalog components, panels, and fields without mutating catalog items.';

COMMENT ON COLUMN dyno_form.form_panel.id IS
'Primary row identifier (UUID). Immutable technical identity.';

COMMENT ON COLUMN dyno_form.form_panel.tenant_id IS
'Tenant boundary. All form panels are scoped to a tenant for isolation and access control.';

COMMENT ON COLUMN dyno_form.form_panel.form_id IS
'Owning form ID. The form that this panel belongs to.';

COMMENT ON COLUMN dyno_form.form_panel.panel_key IS
'Stable identifier for this panel within (tenant_id, form_id). Used by builders/APIs for deterministic lookup.';

COMMENT ON COLUMN dyno_form.form_panel.panel_label IS
'Human-readable label shown in UI. Optional.';

COMMENT ON COLUMN dyno_form.form_panel.ui_config IS
'JSONB UI configuration for layout, styling, and container-level rendering hints for the form panel.';

COMMENT ON COLUMN dyno_form.form_panel.nested_overrides IS
'JSONB document containing selector-addressed PATCH overrides applied to embedded component trees within this form panel. Used to customize catalog components, nested panels, and fields without forking or modifying catalog definitions. Enforced by jsonb_matches_schema.';

COMMENT ON COLUMN dyno_form.form_panel.created_at IS
'Row creation timestamp.';

COMMENT ON COLUMN dyno_form.form_panel.updated_at IS
'Row last-updated timestamp. Typically maintained by application code or a trigger.';

COMMENT ON COLUMN dyno_form.form_panel.created_by IS
'Optional actor identifier (username/service) that created the row.';

COMMENT ON COLUMN dyno_form.form_panel.updated_by IS
'Optional actor identifier (username/service) that last updated the row.';



-- ----------------------------------------------------------------------
-- Table: dyno_form.form_panel_field
-- ----------------------------------------------------------------------
-- PURPOSE
--   Defines a non-reusable field realization placed directly onto a form panel.
--
--   This table is intentionally very similar to dyno_form.component_panel_field,
--   but it lives in the form domain (form definitions are not reusable like catalog
--   components). A form_panel_field represents a concrete field instance as used
--   by a specific form, with its own imprinted and editable field_config.
--
--   Key idea:
--     - field_def_id is a provenance and reset source (optional conceptually),
--       but the effective definition used by the form lives in field_config.
--     - Editing the field inside a form updates field_config and does not mutate
--       the catalog field_def.
--
-- CORE CONCEPTS
--   - Composition (form_panel + field_def):
--       A form panel contains zero or more fields. Each row represents one field
--       instance placed on that panel, sourced from a catalog field_def.
--   - Ordering:
--       field_order controls default tab/display ordering within the form panel.
--   - UI configuration overrides:
--       field_config.field.ui_config is the imprinted base.
--       form_panel_field.ui_config is an override/augmentation applied in the
--       context of this specific placement.
--   - Imprinting (field_config):
--       field_config is a JSONB snapshot that can fully represent the effective
--       field_def and its options at the time the field was placed on the form.
--       Edits modify field_config, not field_def.
--   - Hashing:
--       * field_config_hash: hash of the current field_config JSONB (detect edits/diff).
--       * source_field_def_hash: hash of the canonical source snapshot from field_def
--         (field_def + field_def_option) at imprint time (detect catalog drift).
--
-- IMPORTANT INVARIANTS
--   - tenant_id scopes data to a tenant boundary.
--   - panel_id must belong to the same tenant_id (tenant-safe FK).
--   - field_def_id must belong to the same tenant_id (tenant-safe FK).
--   - A given (tenant_id, panel_id, field_def_id) is unique to prevent accidental
--     duplicate placement of the same field_def on the same form panel.
--   - field_order, when provided, must be >= 0.
--   - field_config must conform to the JSON schema enforced by jsonb_matches_schema.
--   - Hash columns are typically maintained by application logic or triggers.
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_form.form_panel_field (
    -- ------------------------------------------------------------------
    -- Primary identity
    -- ------------------------------------------------------------------
    id UUID PRIMARY KEY,

    -- ------------------------------------------------------------------
    -- Tenant boundary and owning form panel
    -- ------------------------------------------------------------------
    tenant_id UUID NOT NULL,

    -- The form panel this field belongs to.
    panel_id UUID NOT NULL,

    -- The catalog field definition used as the source for this field placement.
    -- This is provenance and reset source. The effective definition used by the
    -- form lives in field_config (imprinted snapshot).
    field_def_id UUID NOT NULL,

    -- Default display/tab order within the form panel.
    -- Null means "unspecified" (UI/service may apply a default ordering strategy).
    field_order INTEGER,

    -- Optional UI overrides applied for this specific placement on the form panel.
    -- This is layered on top of field_config.field.ui_config.
    ui_config JSONB,

    -- ------------------------------------------------------------------
    -- Imprinted field definition snapshot
    -- ------------------------------------------------------------------
    -- JSONB snapshot representing the effective field definition and options for this
    -- placement. This is the editable copy that can diverge from the catalog field_def.
    --
    -- The schema is enforced via public.jsonb_matches_schema(field_config, <schema>).
    field_config JSONB NOT NULL,

    -- Hash of the current field_config JSONB (typically sha256 hex, 64 chars).
    -- Used to detect edits and support fast diff checks without deep JSON comparison.
    field_config_hash VARCHAR(64),

    -- Hash of the canonical source snapshot from field_def + field_def_option that was
    -- used to imprint field_config initially (typically sha256 hex, 64 chars).
    -- Used to detect when the catalog source changed since imprint (reset candidate).
    source_field_def_hash VARCHAR(64),

    -- Timestamp when field_config was last imprinted from the catalog source.
    last_imprinted_at TIMESTAMPTZ,

    -- ------------------------------------------------------------------
    -- Audit columns
    -- ------------------------------------------------------------------
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- ------------------------------------------------------------------
    -- Constraints
    -- ------------------------------------------------------------------

    -- Supports tenant-safe composite foreign keys from child tables.
    CONSTRAINT ux_form_panel_field_tenant_id
        UNIQUE (tenant_id, id),

    -- Defensive: ordering, when provided, must be non-negative.
    CONSTRAINT ck_form_panel_field_order_non_negative
        CHECK (field_order IS NULL OR field_order >= 0),

    -- Prevent duplicate placement of the same field_def on the same form panel.
    CONSTRAINT uq_form_panel_field_panel_field_def
        UNIQUE (tenant_id, panel_id, field_def_id),

    -- Optional: enforce a single field_order value per panel when field_order is used.
    -- This helps prevent "two fields share order 10" ambiguity.
    -- (Allows multiple NULLs.)
    CONSTRAINT uq_form_panel_field_panel_order
        UNIQUE (tenant_id, panel_id, field_order),

    -- Enforce hash formatting when provided (sha256 hex).
    CONSTRAINT ck_form_panel_field_field_config_hash_format
        CHECK (field_config_hash IS NULL OR field_config_hash ~ '^[0-9a-f]{64}$'),

    CONSTRAINT ck_form_panel_field_source_field_def_hash_format
        CHECK (source_field_def_hash IS NULL OR source_field_def_hash ~ '^[0-9a-f]{64}$'),

    -- Enforce field_config JSON schema.
    -- NOTE: This assumes public.jsonb_matches_schema(instance_jsonb, schema_jsonb) exists.
    CONSTRAINT ck_form_panel_field_field_config_schema
        CHECK (
            public.jsonb_matches_schema(
                field_config,
                $${
                  "$schema": "http://json-schema.org/draft-07/schema#",
                  "title": "DynoCRM Form Panel Field Config",
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["schema_version", "field"],
                  "properties": {
                    "schema_version": { "type": "integer", "minimum": 1 },

                    "field": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": ["field_key", "label", "element_type"],
                      "properties": {
                        "field_def_business_key": { "type": "string", "minLength": 1, "maxLength": 400 },
                        "field_def_version": { "type": "integer", "minimum": 1 },

                        "name": { "type": "string", "minLength": 1, "maxLength": 100 },
                        "description": { "type": ["string", "null"], "maxLength": 1000 },

                        "field_key": { "type": "string", "minLength": 1, "maxLength": 100 },
                        "label": { "type": "string", "minLength": 1, "maxLength": 255 },

                        "category_id": { "type": ["string", "null"], "pattern": "^[0-9a-fA-F-]{36}$" },

                        "data_type": {
                          "type": ["string", "null"],
                          "enum": ["TEXT","NUMBER","BOOLEAN","DATE","DATETIME","SINGLESELECT","MULTISELECT", null]
                        },

                        "element_type": {
                          "type": "string",
                          "enum": ["TEXT","TEXTAREA","DATE","DATETIME","SELECT","MULTISELECT","ACTION"]
                        },

                        "validation": { "type": ["object", "null"] },
                        "ui_config": { "type": ["object", "null"] }
                      }
                    },

                    "options": {
                      "type": ["array", "null"],
                      "items": {
                        "type": "object",
                        "additionalProperties": false,
                        "required": ["option_key", "option_label", "option_order"],
                        "properties": {
                          "option_key": { "type": "string", "minLength": 1, "maxLength": 200 },
                          "option_label": { "type": "string", "minLength": 1, "maxLength": 400 },
                          "option_order": { "type": "integer", "minimum": 0 }
                        }
                      }
                    }
                  }
                }$$::jsonb
            )
        ),

    -- ------------------------------------------------------------------
    -- Foreign keys (tenant-safe)
    -- ------------------------------------------------------------------


    -- Tenant-safe: forces panel_id to belong to same tenant_id.
    -- Requires a UNIQUE/PK on dyno_form.form_panel(tenant_id, id) or equivalent.
    CONSTRAINT fk_form_panel_field_panel_tenant
        FOREIGN KEY (tenant_id, panel_id)
        REFERENCES dyno_form.form_panel (tenant_id, id)
        ON DELETE CASCADE,


    CONSTRAINT fk_form_panel_field_field_def_tenant
        FOREIGN KEY (tenant_id, field_def_id)
        REFERENCES dyno_form.field_def (tenant_id, id)
        ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------------------
-- Common access patterns:
--   - list all fields for a form panel ordered by field_order
--   - join to field_def for reset/provenance workflows
--   - tenant-scoped maintenance queries
--   - diff/reset workflows (hash comparisons)
-- ----------------------------------------------------------------------

-- Fast joins to field_def (reset/provenance).
CREATE INDEX IF NOT EXISTS ix_form_panel_field_field_def
    ON dyno_form.form_panel_field (tenant_id, field_def_id);

-- Optional: JSONB search/filtering on ui_config traits.
CREATE INDEX IF NOT EXISTS ix_form_panel_field_ui_config_gin
    ON dyno_form.form_panel_field
    USING GIN (ui_config);

-- Optional: JSONB search/filtering on field_config traits (debugging, analysis, admin tools).
CREATE INDEX IF NOT EXISTS ix_form_panel_field_field_config_gin
    ON dyno_form.form_panel_field
    USING GIN (field_config);

-- Optional: useful for recency queries and debugging.
CREATE INDEX IF NOT EXISTS ix_form_panel_field_tenant_panel_updated_at
    ON dyno_form.form_panel_field (tenant_id, panel_id, updated_at);

-- Optional: accelerate "is overridden" checks via hash comparisons.
CREATE INDEX IF NOT EXISTS ix_form_panel_field_hashes
    ON dyno_form.form_panel_field (tenant_id, field_config_hash, source_field_def_hash);

-- ----------------------------------------------------------------------
-- Comments
-- ----------------------------------------------------------------------

COMMENT ON TABLE dyno_form.form_panel_field IS
'Non-reusable field realization placed directly on a form panel. Stores an imprinted, editable field_config snapshot (field_def + options) with schema enforcement and hashes for diff/reset workflows.';

COMMENT ON COLUMN dyno_form.form_panel_field.id IS
'Primary row identifier (UUID). Immutable technical identity.';

COMMENT ON COLUMN dyno_form.form_panel_field.tenant_id IS
'Tenant boundary. All rows are scoped to a tenant for isolation and access control.';

COMMENT ON COLUMN dyno_form.form_panel_field.panel_id IS
'Owning form panel ID. The form panel that this field placement belongs to.';

COMMENT ON COLUMN dyno_form.form_panel_field.field_def_id IS
'Source catalog field definition ID (field_def). Used for provenance and reset/re-imprint. The effective field definition for this placement lives in field_config.';

COMMENT ON COLUMN dyno_form.form_panel_field.field_order IS
'Default display/tab order within the form panel. Null means unspecified; otherwise non-negative and unique within (tenant_id, panel_id) when present.';

COMMENT ON COLUMN dyno_form.form_panel_field.ui_config IS
'JSONB UI configuration overrides applied on top of the field_config.field.ui_config for this specific form placement (layout/display hints).';

COMMENT ON COLUMN dyno_form.form_panel_field.field_config IS
'Imprinted JSONB snapshot of the effective field definition for this form placement, including option definitions for select/multiselect. Editable without mutating the source field_def. Enforced by jsonb_matches_schema.';

COMMENT ON COLUMN dyno_form.form_panel_field.field_config_hash IS
'Hash (typically sha256 hex) of the current field_config JSONB. Used to detect edits and support diff workflows efficiently.';

COMMENT ON COLUMN dyno_form.form_panel_field.source_field_def_hash IS
'Hash (typically sha256 hex) of the canonical source snapshot from field_def + field_def_option at the time field_config was last imprinted. Used to detect catalog drift since imprint.';

COMMENT ON COLUMN dyno_form.form_panel_field.last_imprinted_at IS
'Timestamp of the last imprint operation that copied the catalog source definition into field_config.';

COMMENT ON COLUMN dyno_form.form_panel_field.created_at IS
'Row creation timestamp.';

COMMENT ON COLUMN dyno_form.form_panel_field.updated_at IS
'Row last-updated timestamp. Typically maintained by application code or a trigger.';

COMMENT ON COLUMN dyno_form.form_panel_field.created_by IS
'Optional actor identifier (username/service) that created the row.';

COMMENT ON COLUMN dyno_form.form_panel_field.updated_by IS
'Optional actor identifier (username/service) that last updated the row.';


-- ----------------------------------------------------------------------
-- Table: dyno_form.form_submission
-- ----------------------------------------------------------------------
-- PURPOSE
--   Represents a tenant-scoped "submission envelope" for a specific form.
--
--   A submission is intentionally UPDATABLE:
--     - Users/automations can save drafts (update the submission and its values)
--     - Users can submit, and later re-submit (update again + bump submission_version)
--
--   The actual field answers live in dyno_form.form_submission_value
--   (one row per field instance per submission).
--
-- CORE CONCEPTS
--   - Draft vs submitted:
--       * is_submitted = FALSE  => draft (can be saved/updated without being "submitted")
--       * is_submitted = TRUE   => submitted at least once
--
--   - submission_version:
--       Tracks how many times this submission has been submitted.
--       * Draft: submission_version = 0
--       * First submit: submission_version = 1
--       * Re-submit: submission_version increments (2, 3, ...)
--
--       This is an intentional "counter" style field.
--       The application is expected to increment it when a submit action occurs.
--
-- TENANT SAFETY
--   - tenant_id is required.
--   - All parent references are tenant-safe composite foreign keys.
--
-- IMPORTANT INVARIANTS
--   - A submission always belongs to exactly one tenant and one form.
--   - submitted_at and submission_version must align with is_submitted.
--   - archived_at must align with is_archived.
-- ----------------------------------------------------------------------


CREATE TABLE IF NOT EXISTS dyno_form.form_submission (
    -- ------------------------------------------------------------------
    -- Primary identity
    -- ------------------------------------------------------------------

    -- Immutable technical row identifier for this submission envelope.
    id UUID PRIMARY KEY,

    -- ------------------------------------------------------------------
    -- Tenant boundary
    -- ------------------------------------------------------------------

    -- Tenant that owns this submission (hard isolation boundary).
    tenant_id UUID NOT NULL,

    -- ------------------------------------------------------------------
    -- Composition reference
    -- ------------------------------------------------------------------

    -- The form definition that this submission belongs to.
    -- This is tenant-safe: the referenced form must be owned by the same tenant.
    form_id UUID NOT NULL,

    -- ------------------------------------------------------------------
    -- Submission lifecycle
    -- ------------------------------------------------------------------

    -- Indicates whether the submission has been formally submitted at least once.
    --
    -- TRUE  => submitted (submission_version >= 1 and submitted_at is required)
    -- FALSE => draft     (submission_version = 0 and submitted_at must be NULL)
    is_submitted BOOLEAN NOT NULL DEFAULT FALSE,

    -- Timestamp of the most recent submit action.
    -- This is NULL for drafts.
    --
    -- For re-submissions, this is expected to be updated to the latest submission time.
    submitted_at TIMESTAMPTZ,

    -- Monotonic counter of how many times this submission has been submitted.
    --
    -- 0 => draft only (never submitted)
    -- 1 => submitted once
    -- 2 => submitted twice (re-submitted once)
    -- etc.
    --
    -- This is NOT a historical record; it is an operational counter.
    submission_version INTEGER NOT NULL DEFAULT 0,

    -- Archived means "no longer active" but retained for history/audit.
    -- Archiving does not imply the submission cannot be updated; that policy is
    -- application-defined. This schema only enforces timestamp consistency.
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,

    -- Timestamp when the submission was archived (if archived).
    archived_at TIMESTAMPTZ,

    -- ------------------------------------------------------------------
    -- Audit columns
    -- ------------------------------------------------------------------

    -- Row creation timestamp (envelope creation; usually when the draft starts).
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Row last-updated timestamp (should be updated by application logic or trigger).
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Optional actor identifier (username/service) that created the submission.
    created_by VARCHAR(100),

    -- Optional actor identifier (username/service) that last updated the submission.
    updated_by VARCHAR(100),

    -- ------------------------------------------------------------------
    -- Constraints
    -- ------------------------------------------------------------------

    -- Canonical tenant-safe helper unique constraint.
    -- Supports composite tenant-safe foreign keys from child tables.
    CONSTRAINT ux_form_submission_tenant_id
        UNIQUE (tenant_id, id),

    -- Enforce reasonable bounds on the submission counter.
    -- (0 for drafts; positive integers for submitted states.)
    CONSTRAINT ck_form_submission_version_non_negative
        CHECK (submission_version >= 0),

    -- Ensure submitted_at and submission_version align with is_submitted.
    --
    -- Draft state (not yet submitted):
    --   - is_submitted = FALSE
    --   - submitted_at IS NULL
    --   - submission_version = 0
    --
    -- Submitted state (submitted at least once):
    --   - is_submitted = TRUE
    --   - submitted_at IS NOT NULL
    --   - submission_version >= 1
    CONSTRAINT ck_form_submission_submitted_state_consistency
        CHECK (
            (is_submitted = FALSE AND submitted_at IS NULL AND submission_version = 0)
            OR
            (is_submitted = TRUE  AND submitted_at IS NOT NULL AND submission_version >= 1)
        ),

    -- Archiving timestamp must align with archived flag.
    CONSTRAINT ck_form_submission_archived_at_consistency
        CHECK (
            (is_archived = TRUE  AND archived_at IS NOT NULL)
         OR (is_archived = FALSE AND archived_at IS NULL)
        ),

    -- Tenant-safe FK to forms.
    CONSTRAINT fk_form_submission_form_tenant
        FOREIGN KEY (tenant_id, form_id)
        REFERENCES dyno_form.form (tenant_id, id)
        ON DELETE CASCADE
);

-- ----------------------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------------------
-- These support common, predictable access patterns without over-indexing:
--   - list submissions for a form (tenant + form)
--   - list recent submissions for a form (tenant + form + updated_at)
-- ----------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS ix_form_submission_tenant_form
    ON dyno_form.form_submission (tenant_id, form_id);

CREATE INDEX IF NOT EXISTS ix_form_submission_tenant_form_updated_at
    ON dyno_form.form_submission (tenant_id, form_id, updated_at);

-- ----------------------------------------------------------------------
-- Comments
-- ----------------------------------------------------------------------

COMMENT ON TABLE dyno_form.form_submission IS
'Updatable tenant-scoped submission envelope for a specific form. Stores lifecycle state (draft vs submitted), last submitted timestamp, and a submission_version counter (0 for drafts; increments per submit/re-submit). Actual field values are stored in dyno_form.form_submission_value (one row per field instance per submission).';

COMMENT ON COLUMN dyno_form.form_submission.id IS
'Primary row identifier (UUID). Immutable technical identity for the submission envelope.';

COMMENT ON COLUMN dyno_form.form_submission.tenant_id IS
'Tenant boundary. Submissions are strictly scoped to a tenant for isolation and access control.';

COMMENT ON COLUMN dyno_form.form_submission.form_id IS
'Identifier of the owning form definition (dyno_form.form.id). Tenant-safe reference: the form must belong to the same tenant_id.';

COMMENT ON COLUMN dyno_form.form_submission.is_submitted IS
'When false, this submission is a draft (submission_version = 0 and submitted_at is NULL). When true, it has been submitted at least once (submission_version >= 1 and submitted_at is required).';

COMMENT ON COLUMN dyno_form.form_submission.submitted_at IS
'Timestamp of the most recent submit action. NULL for drafts. Updated on re-submit to reflect the latest submission time.';

COMMENT ON COLUMN dyno_form.form_submission.submission_version IS
'Monotonic counter of how many times the submission has been submitted. Drafts must be 0. First submit sets it to 1. Each re-submit increments it (2, 3, ...).';

COMMENT ON COLUMN dyno_form.form_submission.is_archived IS
'When true, the submission is archived (retained for history/audit but not actively used). Timestamp consistency is enforced via archived_at.';

COMMENT ON COLUMN dyno_form.form_submission.archived_at IS
'Timestamp when the submission was archived. Must be non-null only when is_archived is true.';

COMMENT ON COLUMN dyno_form.form_submission.created_at IS
'Row creation timestamp (typically when the draft submission was first created).';

COMMENT ON COLUMN dyno_form.form_submission.updated_at IS
'Row last-updated timestamp (updated by application logic or a trigger).';

COMMENT ON COLUMN dyno_form.form_submission.created_by IS
'Optional actor identifier (username/service) that created the submission envelope.';

COMMENT ON COLUMN dyno_form.form_submission.updated_by IS
'Optional actor identifier (username/service) that last updated the submission envelope.';


-- ----------------------------------------------------------------------
-- Table: dyno_form.form_submission_value
-- ----------------------------------------------------------------------
-- PURPOSE
--   Stores captured values for a form submission in a flat, query-friendly shape
--   (one row per field instance per submission).
--
--   Because the storage is intentionally flat, each row also stores a fully
--   qualified field path (field_path) that identifies the field instance within
--   the form definition tree at the time of submission.
--
--   This solves two practical problems:
--     1) Stable identification across nested structures:
--          The same field_def may appear multiple times across different panels
--          or embedded components. field_path disambiguates instances.
--     2) Human and operational readability:
--          field_path allows support, exports, and analytics pipelines to
--          understand where the value came from without reconstructing the full
--          component tree at query time.
--
-- CORE CONCEPTS
--   - Dual placement model (exactly one path):
--       A captured value comes from either:
--         A) a direct field placed on a form panel (form_panel_field_id)
--         B) a field inside a component placed on a form panel
--            (form_panel_component_id + component_panel_field_id)
--   - Fully qualified path:
--       field_path is a deterministic dot-separated path from the form root
--       to the field instance. It is stored redundantly for stability and fast
--       lookup.
--
--       Recommended segment convention (example):
--         <form_key>.<form_panel_key>.<field_key>
--         <form_key>.<form_panel_key>.<component_instance_key>.<component_panel_key>.<field_key>
--
--       Notes:
--         - Use stable keys, not labels.
--         - field_key should come from the effective field_config.field.field_key
--           for that specific placement.
--         - component_instance_key should be the stable key of the specific
--           form_panel_component placement (not the catalog component_key alone).
--
-- IMPORTANT INVARIANTS
--   - tenant_id scopes data to a tenant boundary.
--   - Exactly one placement path must be present (direct vs component).
--   - field_path is required, nonblank, and unique per submission.
--   - The placement-specific uniqueness constraints are retained for safety.
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_form.form_submission_value (
    -- ------------------------------------------------------------------
    -- Primary identity
    -- ------------------------------------------------------------------
    id UUID PRIMARY KEY,

    -- ------------------------------------------------------------------
    -- Tenant boundary and owning submission
    -- ------------------------------------------------------------------
    tenant_id UUID NOT NULL,
    form_submission_id UUID NOT NULL,

    -- Underlying catalog field definition for this value (provenance / analytics).
    -- This may be useful for grouping by field type, even though the actual
    -- field instance is identified by field_path + placement references.
    field_def_id UUID NOT NULL,

    -- ------------------------------------------------------------------
    -- Fully qualified field instance path (required)
    -- ------------------------------------------------------------------
    -- Deterministic dot-separated path to the field instance within the form tree
    -- at the time of submission. This is the primary disambiguator for flat storage.
    --
    -- Examples:
    --   my_form.my_form_panel.email
    --   my_form.my_form_panel.address_component_1.address_panel.state
    --
    -- The exact segment scheme is a product contract. Keep it stable once released.
    field_path VARCHAR(800) NOT NULL,

    -- ------------------------------------------------------------------
    -- Placement references (exactly one path)
    -- ------------------------------------------------------------------

    -- Direct field placement reference (field placed directly on a form panel).
    form_panel_field_id UUID,

    -- Component field placement reference (field inside an embedded component).
    form_panel_component_id UUID,
    component_panel_field_id UUID,

    -- ------------------------------------------------------------------
    -- Captured value
    -- ------------------------------------------------------------------
    -- Captured value (data shape depends on field_def.data_type).
    -- Stored as JSONB to support:
    --   - scalar values (text, number, boolean)
    --   - structured values (dates/datetimes as ISO strings)
    --   - arrays for MULTISELECT
    --   - future extensions (tokens, references, etc.)
    value JSONB,

    -- ------------------------------------------------------------------
    -- Audit columns
    -- ------------------------------------------------------------------
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- ------------------------------------------------------------------
    -- Constraints
    -- ------------------------------------------------------------------

    -- Defensive: prevent empty/whitespace-only paths.
    CONSTRAINT ck_form_submission_value_field_path_nonblank
        CHECK (length(btrim(field_path)) > 0),

    -- Basic format guardrail: dot-separated key segments (allows hyphen and underscore).
    -- This does not enforce segment semantics, only shape.
    CONSTRAINT ck_form_submission_value_field_path_format
        CHECK (field_path ~ '^[A-Za-z0-9_\\-]+(\\.[A-Za-z0-9_\\-]+)+$'),

    -- Exactly one placement path must be set.
    CONSTRAINT ck_form_submission_value_path_exclusive
        CHECK (
            -- direct placement
            (
              form_panel_field_id IS NOT NULL
              AND form_panel_component_id IS NULL
              AND component_panel_field_id IS NULL
            )
            OR
            -- component placement
            (
              form_panel_field_id IS NULL
              AND form_panel_component_id IS NOT NULL
              AND component_panel_field_id IS NOT NULL
            )
        ),

    -- Uniqueness: one row per field instance per submission, identified by field_path.
    -- This is the primary uniqueness guarantee for the flat storage model.
    -- form_submission_id will always be used in seaches so this CONSTRAINT is sufficient
    CONSTRAINT uq_form_submission_value_submission_field_path
        UNIQUE (tenant_id, form_submission_id, field_path)
        DEFERRABLE INITIALLY DEFERRED,

    -- Uniqueness: direct field value per submission (retained as a safety net).
    -- form_submission_id will always be used in seaches so this CONSTRAINT is sufficient
    CONSTRAINT uq_form_submission_value_direct
        UNIQUE (tenant_id, form_submission_id, form_panel_field_id)
        DEFERRABLE INITIALLY DEFERRED,

    -- Uniqueness: component field value per submission (retained as a safety net). 
    -- form_submission_id will always be used in seaches so this CONSTRAINT is sufficient
    CONSTRAINT uq_form_submission_value_component
        UNIQUE (tenant_id, form_submission_id,
                form_panel_component_id, component_panel_field_id)
        DEFERRABLE INITIALLY DEFERRED,

    -- ------------------------------------------------------------------
    -- Foreign keys (tenant-safe)
    -- ------------------------------------------------------------------

    CONSTRAINT fk_form_submission_value_submission_tenant
        FOREIGN KEY (tenant_id, form_submission_id)
        REFERENCES dyno_form.form_submission (tenant_id, id)
        ON DELETE CASCADE,

    CONSTRAINT fk_form_submission_value_field_def_tenant
        FOREIGN KEY (tenant_id, field_def_id)
        REFERENCES dyno_form.field_def (tenant_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_form_submission_value_form_panel_field_tenant
        FOREIGN KEY (tenant_id, form_panel_field_id)
        REFERENCES dyno_form.form_panel_field (tenant_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_form_submission_value_form_panel_component_tenant
        FOREIGN KEY (tenant_id, form_panel_component_id)
        REFERENCES dyno_form.form_panel_component (tenant_id, id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_form_submission_value_component_panel_field_tenant
        FOREIGN KEY (tenant_id, component_panel_field_id)
        REFERENCES dyno_form.component_panel_field (tenant_id, id)
        ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------
-- Indexes for dyno_form.form_submission_value
-- ----------------------------------------------------------------------

-- Fast tenant scoping.
CREATE INDEX IF NOT EXISTS ix_form_submission_value_tenant_id
    ON dyno_form.form_submission_value (tenant_id);

-- Retrieve all values for a submission.
CREATE INDEX IF NOT EXISTS ix_form_submission_value_submission
    ON dyno_form.form_submission_value (tenant_id, form_submission_id);

-- Fast lookup of a specific field instance by fully qualified path.
CREATE INDEX IF NOT EXISTS ix_form_submission_value_submission_field_path
    ON dyno_form.form_submission_value (tenant_id, form_submission_id, field_path);

-- Filter values by field_def across submissions.
CREATE INDEX IF NOT EXISTS ix_form_submission_value_field_def
    ON dyno_form.form_submission_value (tenant_id, field_def_id);

-- Lookup direct field values for a specific panel placement.
CREATE INDEX IF NOT EXISTS ix_form_submission_value_panel_field
    ON dyno_form.form_submission_value (tenant_id, form_panel_field_id)
    WHERE form_panel_field_id IS NOT NULL;

-- Lookup component field values for a specific component placement.
CREATE INDEX IF NOT EXISTS ix_form_submission_value_component_field
    ON dyno_form.form_submission_value (
        tenant_id,
        form_panel_component_id,
        component_panel_field_id
    )
    WHERE form_panel_component_id IS NOT NULL;

-- JSONB GIN index for value (useful for searching within captured data).
CREATE INDEX IF NOT EXISTS ix_form_submission_value_value_gin
    ON dyno_form.form_submission_value
    USING GIN (value);

-- Recency queries.
CREATE INDEX IF NOT EXISTS ix_form_submission_value_tenant_submission_updated_at
    ON dyno_form.form_submission_value (tenant_id, form_submission_id, updated_at);

-- ----------------------------------------------------------------------
-- Column comments for dyno_form.form_submission_value
-- ----------------------------------------------------------------------

COMMENT ON TABLE dyno_form.form_submission_value IS
'Stores captured values for a specific field instance within a form submission. Each row represents one field instance, identified by field_path. The instance is either a direct field on a form panel (form_panel_field_id) or a field inside a component placed on a form panel (form_panel_component_id + component_panel_field_id). Exactly one of these placement paths must be non-null.';

COMMENT ON COLUMN dyno_form.form_submission_value.id IS
'Primary row identifier (UUID). Immutable technical identity.';

COMMENT ON COLUMN dyno_form.form_submission_value.tenant_id IS
'Tenant boundary. All rows are scoped to a tenant for isolation and access control.';

COMMENT ON COLUMN dyno_form.form_submission_value.form_submission_id IS
'Identifier of the form submission this value belongs to.';

COMMENT ON COLUMN dyno_form.form_submission_value.field_def_id IS
'Identifier of the underlying catalog field_def used as the provenance/source type for this field instance. Useful for analytics and grouping by field type.';

COMMENT ON COLUMN dyno_form.form_submission_value.field_path IS
'Fully qualified dot-separated path identifying the field instance within the form definition tree at the time of submission. Primary disambiguator for flat storage and required to be unique per submission.';

COMMENT ON COLUMN dyno_form.form_submission_value.form_panel_field_id IS
'Reference to a direct field placement on a form panel. NULL when the value comes from a field inside a component.';

COMMENT ON COLUMN dyno_form.form_submission_value.form_panel_component_id IS
'Reference to a specific component placement on a form panel. Used together with component_panel_field_id to identify a field inside a component.';

COMMENT ON COLUMN dyno_form.form_submission_value.component_panel_field_id IS
'Identifier of the field inside a catalog component (component_panel_field). Used together with form_panel_component_id.';

COMMENT ON COLUMN dyno_form.form_submission_value.value IS
'Captured field value stored as JSONB. Shape depends on field_def.data_type (e.g., string for TEXT, number for NUMBER, boolean for BOOLEAN, array for MULTISELECT).';

COMMENT ON COLUMN dyno_form.form_submission_value.created_at IS
'Row creation timestamp.';

COMMENT ON COLUMN dyno_form.form_submission_value.updated_at IS
'Row last-updated timestamp. Typically maintained by application code or a trigger.';

COMMENT ON COLUMN dyno_form.form_submission_value.created_by IS
'Optional actor identifier (username/service) that created the row.';

COMMENT ON COLUMN dyno_form.form_submission_value.updated_by IS
'Optional actor identifier (username/service) that last updated the row.';
-- END original form_schema.sql
-- ======================================================================
-- PHASE 1: Correctness fixes and hardening
-- ======================================================================


-- ----------------------------------------------------------------------
-- Table: dyno_form.field_def_option
-- ----------------------------------------------------------------------
COMMENT ON COLUMN dyno_form.field_def_option.tenant_id IS
    'Tenant boundary. Options are scoped to a tenant for isolation and customization.';
COMMENT ON COLUMN dyno_form.field_def_option.field_def_id IS
    'Identifier of the parent field definition this option belongs to.';
COMMENT ON COLUMN dyno_form.field_def_option.option_key IS
    'Stable key used in API values. Must be unique within a field definition and tenant.';
COMMENT ON COLUMN dyno_form.field_def_option.option_label IS
    'Display value shown in UI for this option.';
COMMENT ON COLUMN dyno_form.field_def_option.option_order IS
    'Ordering index controlling display order in UI. Must be non-negative and unique within (tenant_id, field_def_id).';
COMMENT ON COLUMN dyno_form.field_def_option.created_at IS
    'Row creation timestamp.';
COMMENT ON COLUMN dyno_form.field_def_option.created_by IS
    'Optional actor identifier (username/service) that created the row.';




-- ----------------------------------------------------------------------
-- Table: dyno_form.form_panel
-- ----------------------------------------------------------------------
COMMENT ON COLUMN dyno_form.form_panel.id IS
    'Primary row identifier (UUID). Immutable technical identity.';
COMMENT ON COLUMN dyno_form.form_panel.tenant_id IS
    'Tenant boundary. All form panels are scoped to a tenant for isolation and access control.';
COMMENT ON COLUMN dyno_form.form_panel.form_id IS
    'Owning form ID. The form that this panel belongs to.';
COMMENT ON COLUMN dyno_form.form_panel.panel_key IS
    'Stable identifier for this panel within (tenant_id, form_id). Used by builders and APIs for deterministic lookup.';
COMMENT ON COLUMN dyno_form.form_panel.panel_label IS
    'Human-readable label shown in UI. Optional; if provided, must be non-blank.';
COMMENT ON COLUMN dyno_form.form_panel.ui_config IS
    'JSONB UI configuration for layout, styling, and container-level rendering hints. Uses jsonb_merge_default semantics for PATCH merges: arrays are replaced and null values remove keys.';
COMMENT ON COLUMN dyno_form.form_panel.nested_overrides IS
    'JSONB document containing selector-addressed PATCH overrides applied to embedded component trees within this form panel. Uses jsonb_merge_default semantics for patch merges; arrays are replaced and null values remove keys.';
COMMENT ON COLUMN dyno_form.form_panel.created_at IS
    'Row creation timestamp.';
COMMENT ON COLUMN dyno_form.form_panel.updated_at IS
    'Row last-updated timestamp. Typically maintained by application code or a trigger.';
COMMENT ON COLUMN dyno_form.form_panel.created_by IS
    'Optional actor identifier (username/service) that created the row.';
COMMENT ON COLUMN dyno_form.form_panel.updated_by IS
    'Optional actor identifier (username/service) that last updated the row.';

-- ----------------------------------------------------------------------
-- Table: dyno_form.form_panel_field
-- ----------------------------------------------------------------------
COMMENT ON COLUMN dyno_form.form_panel_field.id IS
    'Primary row identifier (UUID). Immutable technical identity.';
COMMENT ON COLUMN dyno_form.form_panel_field.tenant_id IS
    'Tenant boundary. All rows are scoped to a tenant for isolation and access control.';
COMMENT ON COLUMN dyno_form.form_panel_field.panel_id IS
    'Owning form panel ID (dyno_form.form_panel.id) that this field placement belongs to.';
COMMENT ON COLUMN dyno_form.form_panel_field.field_def_id IS
    'Identifier of the catalog field definition (dyno_form.field_def.id) used as the source for this field placement.';
COMMENT ON COLUMN dyno_form.form_panel_field.field_order IS
    'Display/tab order within the form panel. Null means unspecified; otherwise a non-negative integer unique within (tenant_id, panel_id).';
COMMENT ON COLUMN dyno_form.form_panel_field.ui_config IS
    'JSONB UI configuration overrides applied on top of the imprinted field_config.field.ui_config for this specific form placement. Uses jsonb_merge_default semantics for PATCH merges: arrays are replaced and null values remove keys.';
COMMENT ON COLUMN dyno_form.form_panel_field.field_config IS
    'Imprinted JSONB snapshot of the effective field definition for this form placement, including options. Enforced by jsonb_matches_schema. Uses jsonb_merge_default semantics for PATCH merges.';
COMMENT ON COLUMN dyno_form.form_panel_field.field_config_hash IS
    'SHA-256 hash (64 hex characters) of the current field_config JSON. Used to detect edits and support diff workflows.';
COMMENT ON COLUMN dyno_form.form_panel_field.source_field_def_hash IS
    'SHA-256 hash (64 hex characters) of the canonical source snapshot from field_def + field_def_option at imprint time. Used to detect catalog drift.';
COMMENT ON COLUMN dyno_form.form_panel_field.last_imprinted_at IS
    'Timestamp when field_config was last imprinted from the catalog source.';
COMMENT ON COLUMN dyno_form.form_panel_field.created_at IS
    'Row creation timestamp.';
COMMENT ON COLUMN dyno_form.form_panel_field.updated_at IS
    'Row last-updated timestamp. Typically maintained by application code or a trigger.';
COMMENT ON COLUMN dyno_form.form_panel_field.created_by IS
    'Optional actor identifier (username/service) that created the row.';
COMMENT ON COLUMN dyno_form.form_panel_field.updated_by IS
    'Optional actor identifier (username/service) that last updated the row.';


-- ----------------------------------------------------------------------
-- Table: dyno_form.form_catalog_category
-- ----------------------------------------------------------------------
COMMENT ON COLUMN dyno_form.form_catalog_category.created_at IS
    'Row creation timestamp.';
COMMENT ON COLUMN dyno_form.form_catalog_category.updated_at IS
    'Row last-updated timestamp. Typically maintained by application code or a trigger.';
COMMENT ON COLUMN dyno_form.form_catalog_category.created_by IS
    'Optional actor identifier (username/service) that created the row.';
COMMENT ON COLUMN dyno_form.form_catalog_category.updated_by IS
    'Optional actor identifier (username/service) that last updated the row.';


-- ======================================================================
-- PHASE 2: Marketplace-grade additions
-- ======================================================================

-- ----------------------------------------------------------------------
-- Table: dyno_form.form_panel_component
-- ----------------------------------------------------------------------
-- PURPOSE
--   Represents the placement of a reusable catalog component onto a specific
--   form panel within a tenant-owned form definition.
--
-- CORE CONCEPTS
--   - Instance identity:
--       * Each placement represents a distinct instance of a reusable component.
--       * instance_key provides a stable, deterministic identifier for this
--         component instance within (tenant_id, form_panel_id).
--
--   - Composition boundary:
--       * A form_panel may embed zero or more reusable components.
--       * This table acts as the join/composition layer between:
--           - dyno_form.form_panel (form structure)
--           - dyno_form.component (reusable catalog component)
--
--   - Configuration layering:
--       * ui_config stores placement-level UI overrides.
--       * nested_overrides stores selector-addressed PATCH overrides that apply
--         inside the embedded component tree (fields, panels, actions).
--
-- TENANT SAFETY
--   - tenant_id scopes all rows to a tenant boundary.
--   - All foreign keys are tenant-safe composites to prevent cross-tenant leakage.
--
-- IMPORTANT INVARIANTS
--   - instance_key must be unique within (tenant_id, form_panel_id).
--   - instance_key must be stable and deterministic; it must NEVER be derived
--     from labels or user-facing text.
--   - component_id and form_panel_id must belong to the same tenant_id.
--   - updated_at is maintained by application code or a trigger (not defined here).
-- ----------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS dyno_form.form_panel_component (
    -- ------------------------------------------------------------------
    -- Primary identity
    -- ------------------------------------------------------------------

    -- Immutable technical row identifier.
    id UUID PRIMARY KEY,

    -- ------------------------------------------------------------------
    -- Tenant boundary
    -- ------------------------------------------------------------------

    -- Tenant that owns this component placement.
    tenant_id UUID NOT NULL,

    -- ------------------------------------------------------------------
    -- Composition references
    -- ------------------------------------------------------------------

    -- The form panel on which this component is placed.
    -- Must belong to the same tenant_id.
    form_panel_id UUID NOT NULL,

    -- The reusable catalog component being placed.
    -- Must belong to the same tenant_id.
    component_id UUID NOT NULL,

    -- ------------------------------------------------------------------
    -- Instance identity
    -- ------------------------------------------------------------------

    -- Stable key uniquely identifying this component instance within
    -- (tenant_id, form_panel_id).
    --
    -- Used for:
    --   - field_path construction during submissions
    --   - selector-based override addressing
    --   - deterministic diffing and patch application
    --
    -- MUST be stable and deterministic.
    -- MUST NOT be derived from labels or display text.
    instance_key VARCHAR(200) NOT NULL,

    -- ------------------------------------------------------------------
    -- Configuration overrides
    -- ------------------------------------------------------------------

    -- Optional JSONB UI configuration overrides applied at the placement level.
    -- These overrides are layered on top of the component’s catalog ui_config.
    --
    -- PATCH semantics:
    --   - Objects are merged
    --   - Arrays are replaced
    --   - Null values remove keys
    ui_config JSONB,

    -- Optional JSONB document containing selector-addressed PATCH overrides
    -- that apply inside the embedded component tree.
    --
    -- Used to customize:
    --   - component panels
    --   - component fields
    --   - panel actions
    --
    -- Overrides do NOT mutate the catalog component.
    nested_overrides JSONB,

    -- ------------------------------------------------------------------
    -- Audit columns
    -- ------------------------------------------------------------------

    -- Row creation timestamp.
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Row last-updated timestamp.
    -- Typically maintained by application code or a trigger.
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Optional actor identifier (username/service) that created the row.
    created_by VARCHAR(100),

    -- Optional actor identifier (username/service) that last updated the row.
    updated_by VARCHAR(100),

    -- ------------------------------------------------------------------
    -- Constraints
    -- ------------------------------------------------------------------

    -- Canonical tenant-safe helper unique constraint.
    -- Supports composite tenant-safe foreign keys from child tables.
    CONSTRAINT ux_form_panel_component_tenant_id
        UNIQUE (tenant_id, id),

    -- Ensures instance_key uniqueness within a single form panel.
    -- Prevents ambiguous component instances within the same panel.
    CONSTRAINT uq_form_panel_component_instance_key
        UNIQUE (tenant_id, form_panel_id, instance_key),

    -- ------------------------------------------------------------------
    -- Foreign keys (tenant-safe)
    -- ------------------------------------------------------------------

    -- Tenant-safe FK enforcing form_panel ownership.
    CONSTRAINT fk_form_panel_component_form_panel_tenant
        FOREIGN KEY (tenant_id, form_panel_id)
        REFERENCES dyno_form.form_panel (tenant_id, id)
        ON DELETE CASCADE,

    -- Tenant-safe FK enforcing component ownership.
    CONSTRAINT fk_form_panel_component_component_tenant
        FOREIGN KEY (tenant_id, component_id)
        REFERENCES dyno_form.component (tenant_id, id)
        ON DELETE RESTRICT
);

-- ----------------------------------------------------------------------
-- Indexes
-- ----------------------------------------------------------------------

-- Fast lookup of all component placements for a given form panel.
CREATE INDEX IF NOT EXISTS ix_form_panel_component_tenant_panel
    ON dyno_form.form_panel_component (tenant_id, form_panel_id);

-- Fast lookup of all form placements for a given component.
CREATE INDEX IF NOT EXISTS ix_form_panel_component_tenant_component
    ON dyno_form.form_panel_component (tenant_id, component_id);

-- ----------------------------------------------------------------------
-- Table and column comments
-- ----------------------------------------------------------------------

COMMENT ON TABLE dyno_form.form_panel_component IS
'Placement of a reusable catalog component onto a specific form panel. Acts as the composition layer between form structure and reusable components. Provides a stable instance_key for deterministic addressing, submission path construction, and override patching.';

COMMENT ON COLUMN dyno_form.form_panel_component.id IS
'Primary row identifier (UUID). Immutable technical identity for the component placement.';

COMMENT ON COLUMN dyno_form.form_panel_component.tenant_id IS
'Tenant boundary. All component placements are strictly scoped to a tenant for isolation and access control.';

COMMENT ON COLUMN dyno_form.form_panel_component.form_panel_id IS
'Identifier of the owning form panel (dyno_form.form_panel.id) on which this component is placed.';

COMMENT ON COLUMN dyno_form.form_panel_component.component_id IS
'Identifier of the reusable catalog component (dyno_form.component.id) being placed on the form panel.';

COMMENT ON COLUMN dyno_form.form_panel_component.instance_key IS
'Stable, deterministic key uniquely identifying this component instance within (tenant_id, form_panel_id). Used for field_path construction, selector-based overrides, and diff/reset workflows. Must never be derived from labels.';

COMMENT ON COLUMN dyno_form.form_panel_component.ui_config IS
'Optional JSONB UI configuration overrides applied at the component placement level. PATCH semantics: objects merge, arrays replace, null values remove keys.';

COMMENT ON COLUMN dyno_form.form_panel_component.nested_overrides IS
'Optional JSONB document containing selector-addressed PATCH overrides applied within the embedded component tree (panels, fields, actions) without mutating catalog definitions.';

COMMENT ON COLUMN dyno_form.form_panel_component.created_at IS
'Row creation timestamp.';

COMMENT ON COLUMN dyno_form.form_panel_component.updated_at IS
'Row last-updated timestamp. Typically maintained by application code or a trigger.';

COMMENT ON COLUMN dyno_form.form_panel_component.created_by IS
'Optional actor identifier (username/service) that created the component placement.';

COMMENT ON COLUMN dyno_form.form_panel_component.updated_by IS
'Optional actor identifier (username/service) that last updated the component placement.';


-- ======================================================================
-- PHASE 3: Deterministic JSONB merge utilities
-- ======================================================================

CREATE OR REPLACE FUNCTION dyno_form.jsonb_merge_deterministic(
    target jsonb,
    patch jsonb,
    null_means_remove boolean DEFAULT true,
    array_mode text DEFAULT 'REPLACE'
) RETURNS jsonb
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
DECLARE
    result jsonb := COALESCE(target, '{}'::jsonb);
    key text;
    value jsonb;
    target_val jsonb;
BEGIN
    IF patch IS NULL THEN
        RETURN result;
    END IF;
    IF jsonb_typeof(patch) <> 'object' THEN
        IF jsonb_typeof(patch) = 'array' AND jsonb_typeof(target) = 'array' THEN
            IF upper(array_mode) = 'APPEND' THEN
                RETURN COALESCE(target, '[]'::jsonb) || patch;
            ELSE
                RETURN patch;
            END IF;
        ELSE
            RETURN patch;
        END IF;
    END IF;
    FOR key, value IN SELECT key, value FROM jsonb_each(patch) ORDER BY key LOOP
        target_val := result -> key;
        IF value IS NULL THEN
            IF null_means_remove THEN
                result := result - key;
            ELSE
                result := result || jsonb_build_object(key, NULL);
            END IF;
        ELSE
            IF jsonb_typeof(value) = 'object' AND jsonb_typeof(target_val) = 'object' THEN
                result := result || jsonb_build_object(
                    key,
                    dyno_form.jsonb_merge_deterministic(target_val, value, null_means_remove, array_mode)
                );
            ELSIF jsonb_typeof(value) = 'array' AND jsonb_typeof(target_val) = 'array' THEN
                IF upper(array_mode) = 'APPEND' THEN
                    result := result || jsonb_build_object(key, target_val || value);
                ELSE
                    result := result || jsonb_build_object(key, value);
                END IF;
            ELSE
                result := result || jsonb_build_object(key, value);
            END IF;
        END IF;
    END LOOP;
    RETURN result;
END;
$$;

CREATE OR REPLACE FUNCTION dyno_form.jsonb_merge_default(
    target jsonb,
    patch jsonb
) RETURNS jsonb
LANGUAGE plpgsql
IMMUTABLE
STRICT
AS $$
BEGIN
    RETURN dyno_form.jsonb_merge_deterministic(target, patch, true, 'REPLACE');
END;
$$;

COMMENT ON FUNCTION dyno_form.jsonb_merge_deterministic(jsonb, jsonb, boolean, text) IS
    'Deterministically merges two JSONB documents with configurable null and array semantics. Objects are merged recursively; arrays are either replaced or appended depending on array_mode; nulls remove keys when null_means_remove is true or set keys to JSON null otherwise. Keys are processed in sorted order for deterministic results.';
COMMENT ON FUNCTION dyno_form.jsonb_merge_default(jsonb, jsonb) IS
    'Convenience wrapper around jsonb_merge_deterministic that uses platform defaults: arrays are replaced and null values remove keys.';


-- ======================================================================
-- Block updates and deletes to published objects
-- ======================================================================
--
-- PURPOSE
-- -------
-- Enforces immutability for artifacts that have been marked as published.
--
-- Once an artifact is published, it becomes a stable, externally visible
-- contract (e.g. marketplace artifact, provider catalog entry, or
-- production form definition). Allowing in-place updates or deletes would:
--
--   - break referential and behavioral expectations
--   - invalidate cached client behavior and builder assumptions
--   - make marketplace upgrades and drift detection unreliable
--   - complicate audit, support, and rollback workflows
--   - risk loss or mutation of data that depends on the published shape
--
-- This trigger-based enforcement guarantees that *no UPDATE or DELETE*
-- can modify a published row, regardless of which application, service,
-- or script attempts the change.
--
-- DESIGN NOTES
-- ------------
-- * Implemented as BEFORE UPDATE / BEFORE DELETE triggers so violations are
--   caught early and abort the statement.
-- * Uses OLD.is_published to ensure that once a row is published, it cannot
--   be modified or removed in place.
-- * Applies uniformly across all artifact tables that share the
--   `is_published` semantic.
-- * Encourages a clone-and-edit or versioning workflow instead of mutation.
--
-- FUTURE CONSIDERATIONS
-- ---------------------
-- * You mentioned a potential exception for archived objects. That is TBD.
--   This policy currently prioritizes protecting existing data and stability.
--
-- ======================================================================


-- ----------------------------------------------------------------------
-- Trigger function: dyno_form.block_writes_when_published
-- ----------------------------------------------------------------------
--
-- FUNCTIONALITY
-- -------------
-- Blocks UPDATE and DELETE operations on rows that are already published
-- (is_published = true).
--
-- The function is table-agnostic and relies only on:
--   - the presence of an `is_published` boolean column
--   - row-level trigger context (OLD / NEW)
--   - trigger operation (TG_OP)
--
-- BEHAVIOR
-- --------
-- * If OLD.is_published is true:
--     - Raise an exception
--     - Abort the UPDATE or DELETE
-- * If OLD.is_published is false:
--     - Allow the operation to proceed normally
--
-- ERROR SEMANTICS
-- ---------------
-- * Uses SQLSTATE `check_violation` to clearly signal a data integrity rule
--   violation rather than a generic runtime error.
-- * Includes schema, table name, and operation in the error detail for
--   easier debugging and log correlation.
-- * Provides a human-readable hint guiding the correct workflow
--   (clone or unpublish before editing).
--
-- EXTENSIBILITY
-- -------------
-- If future requirements introduce:
--   - admin bypass for migrations/support
--   - archived exceptions
--   - partial mutability of specific columns
--   - versioned publishing (new row per publish)
--
-- this function can be extended or wrapped without changing existing triggers.
--
-- ----------------------------------------------------------------------

CREATE OR REPLACE FUNCTION dyno_form.block_writes_when_published()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  -- Guardrail: block writes to rows that are already published.
  IF OLD.is_published IS TRUE THEN
    RAISE EXCEPTION '% is not allowed for published artifacts.', TG_OP
      USING
        -- Signals a constraint-style violation rather than a runtime error.
        ERRCODE = 'check_violation',

        -- Includes table identity and operation for precise diagnostics.
        DETAIL  = format(
                    'Operation=%s Table=%I.%I row is published',
                    TG_OP,
                    TG_TABLE_SCHEMA,
                    TG_TABLE_NAME
                  ),

        -- Directs developers and users toward the intended workflow.
        HINT    = 'Clone or unpublish the artifact before modifying or deleting it.';
  END IF;

  -- Allow UPDATE to proceed by returning NEW.
  IF TG_OP = 'UPDATE' THEN
    RETURN NEW;
  END IF;

  -- Allow DELETE to proceed by returning OLD.
  RETURN OLD;
END;
$$;

COMMENT ON FUNCTION dyno_form.block_writes_when_published() IS
'Trigger function that enforces immutability for published artifacts. When OLD.is_published = true, it blocks UPDATE and DELETE operations by raising a check_violation exception. Intended for attachment via BEFORE UPDATE/DELETE triggers on top-level artifact tables that include an is_published boolean (e.g., field definitions, components, forms). Provides clear diagnostics (schema/table/operation) and a workflow hint directing callers to clone or unpublish before modifying.';


-- ----------------------------------------------------------------------
-- Trigger attachments (top-level published artifacts)
-- ----------------------------------------------------------------------
--
-- These triggers apply the immutability rule to all core artifact tables
-- that support publishing semantics.
--
-- Covered tables (top-level published objects):
--   - dyno_form.field_def
--   - dyno_form.component
--   - dyno_form.form
--
-- Each table receives:
--   - BEFORE UPDATE trigger
--   - BEFORE DELETE trigger
--
-- NOTE
-- ----
-- All of these tables must share the same `is_published` meaning:
-- once true, the row represents a stable, externally consumable artifact.
-- ----------------------------------------------------------------------

-- dyno_form.field_def
CREATE TRIGGER tr_block_writes_when_published
BEFORE UPDATE ON dyno_form.field_def
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_published();

CREATE TRIGGER tr_block_deletes_when_published
BEFORE DELETE ON dyno_form.field_def
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_published();

-- dyno_form.component
CREATE TRIGGER tr_block_writes_when_published
BEFORE UPDATE ON dyno_form.component
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_published();

CREATE TRIGGER tr_block_deletes_when_published
BEFORE DELETE ON dyno_form.component
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_published();

-- dyno_form.form
CREATE TRIGGER tr_block_writes_when_published
BEFORE UPDATE ON dyno_form.form
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_published();

CREATE TRIGGER tr_block_deletes_when_published
BEFORE DELETE ON dyno_form.form
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_published();


-- ======================================================================
-- Block updates and deletes to form structure when the parent form is published
-- ======================================================================
--
-- PURPOSE
-- -------
-- Enforces immutability of a form’s structural hierarchy once the parent
-- form has been marked as published.
--
-- This prevents in-place modification or deletion of:
--   - form panels
--   - fields placed directly on form panels
--   - embedded component placements within form panels
--
-- once the owning form is published.
--
-- Why delete is also blocked:
--   - Deleting structural nodes from a published form changes its effective
--     schema and breaks stability guarantees.
--   - Published forms must remain reproducible over time for support/audit
--     and to protect submission interpretation.
--
-- SCOPE
-- -----
-- Covered child tables (form structure):
--   - dyno_form.form_panel
--   - dyno_form.form_panel_field
--   - dyno_form.form_panel_component
--
-- DESIGN NOTES
-- ------------
-- * Implemented as a BEFORE UPDATE / BEFORE DELETE trigger on each child table.
-- * Child tables do not need is_published themselves; publish state is derived
--   from the owning dyno_form.form.
-- * Tenant isolation is enforced via (tenant_id, id) join constraints.
--
-- ======================================================================


-- ----------------------------------------------------------------------
-- Trigger function: dyno_form.block_writes_when_parent_form_published
-- ----------------------------------------------------------------------
--
-- FUNCTIONALITY
-- -------------
-- Blocks UPDATE and DELETE operations on form-related child rows when their
-- owning form is already published.
--
-- PARENT RESOLUTION STRATEGY
-- --------------------------
-- 1) dyno_form.form_panel
--    - child row contains form_id directly
--    - lookup: form(tenant_id, id) = (OLD.tenant_id, OLD.form_id)
--
-- 2) dyno_form.form_panel_field, dyno_form.form_panel_component
--    - child row contains panel_id
--    - resolve form via form_panel then join to form
--
-- SAFETY GUARDRAIL
-- ---------------
-- If this function is attached to an unsupported table name, it raises an
-- exception. This avoids silent misconfiguration that could weaken the
-- immutability policy.
--
-- ----------------------------------------------------------------------

CREATE OR REPLACE FUNCTION dyno_form.block_writes_when_parent_form_published()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  parent_published boolean;
BEGIN
  -- Resolve parent form publish state based on triggering table.
  IF TG_TABLE_NAME = 'form_panel' THEN
    SELECT f.is_published
      INTO parent_published
      FROM dyno_form.form f
     WHERE f.tenant_id = OLD.tenant_id
       AND f.id = OLD.form_id;

  ELSIF TG_TABLE_NAME IN ('form_panel_field', 'form_panel_component') THEN
    SELECT f.is_published
      INTO parent_published
      FROM dyno_form.form_panel p
      JOIN dyno_form.form f
        ON f.tenant_id = p.tenant_id
       AND f.id = p.form_id
     WHERE p.tenant_id = OLD.tenant_id
       AND p.id = OLD.panel_id;

  ELSE
    -- Misconfiguration guardrail: do not silently allow writes.
    RAISE EXCEPTION 'Trigger function % attached to unsupported table %.%',
      'dyno_form.block_writes_when_parent_form_published()',
      TG_TABLE_SCHEMA,
      TG_TABLE_NAME
      USING ERRCODE = 'invalid_parameter_value';
  END IF;

  -- Enforce immutability if the parent form is published.
  IF parent_published IS TRUE THEN
    RAISE EXCEPTION '% is not allowed: parent form is published.', TG_OP
      USING
        ERRCODE = 'check_violation',
        DETAIL  = format(
                    'Operation=%s Table=%I.%I parent form is published',
                    TG_OP,
                    TG_TABLE_SCHEMA,
                    TG_TABLE_NAME
                  ),
        HINT    = 'Clone the form (or edit an unpublished draft) before modifying or deleting its panels or fields.';
  END IF;

  -- Allow UPDATE to proceed by returning NEW.
  IF TG_OP = 'UPDATE' THEN
    RETURN NEW;
  END IF;

  -- Allow DELETE to proceed by returning OLD.
  RETURN OLD;
END;
$$;


COMMENT ON FUNCTION dyno_form.block_writes_when_parent_form_published() IS
'Trigger function that enforces immutability of form structure rows when the owning parent form is published. Used as a BEFORE UPDATE/DELETE trigger on form child tables (e.g., form_panel, form_panel_field, form_panel_component). Resolves parent publish state using tenant-safe joins (either directly via form_id or indirectly via panel_id -> form_panel -> form). If the parent form is published, blocks the write with check_violation. Includes a guardrail that raises invalid_parameter_value if attached to an unsupported table to prevent silent misconfiguration.';

-- ----------------------------------------------------------------------
-- Trigger attachments (form structure children)
-- ----------------------------------------------------------------------
--
-- Each table receives:
--   - BEFORE UPDATE trigger
--   - BEFORE DELETE trigger
--
-- ----------------------------------------------------------------------

-- dyno_form.form_panel
CREATE TRIGGER tr_block_writes_when_parent_form_published
BEFORE UPDATE ON dyno_form.form_panel
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_parent_form_published();

CREATE TRIGGER tr_block_deletes_when_parent_form_published
BEFORE DELETE ON dyno_form.form_panel
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_parent_form_published();

-- dyno_form.form_panel_field
CREATE TRIGGER tr_block_writes_when_parent_form_published
BEFORE UPDATE ON dyno_form.form_panel_field
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_parent_form_published();

CREATE TRIGGER tr_block_deletes_when_parent_form_published
BEFORE DELETE ON dyno_form.form_panel_field
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_parent_form_published();

-- dyno_form.form_panel_component
CREATE TRIGGER tr_block_writes_when_parent_form_published
BEFORE UPDATE ON dyno_form.form_panel_component
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_parent_form_published();

CREATE TRIGGER tr_block_deletes_when_parent_form_published
BEFORE DELETE ON dyno_form.form_panel_component
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_parent_form_published();


-- ======================================================================
-- Block updates and deletes to component structure when the parent component is published
-- ======================================================================
--
-- PURPOSE
-- -------
-- Enforces immutability for the structural tree beneath a reusable component
-- once that component has been published.
--
-- This prevents in-place modification or deletion of:
--   - component panels
--   - fields placed on component panels
--
-- once the owning component is published.
--
-- Why delete is also blocked:
--   - Deleting panel/field nodes changes the published component definition.
--   - Published components may be referenced by forms; structural deletion would
--     break reproducibility and stability guarantees.
--
-- SCOPE
-- -----
-- Covered child tables (component structure):
--   - dyno_form.component_panel
--   - dyno_form.component_panel_field
--
-- DESIGN NOTES
-- ------------
-- * Implemented as a BEFORE UPDATE / BEFORE DELETE trigger on each child table.
-- * Child tables do not need is_published themselves; publish state is derived
--   from the owning dyno_form.component.
-- * Tenant isolation is enforced via tenant-safe joins.
--
-- ======================================================================


-- ----------------------------------------------------------------------
-- Trigger function: dyno_form.block_writes_when_parent_component_published
-- ----------------------------------------------------------------------
--
-- FUNCTIONALITY
-- -------------
-- Blocks UPDATE and DELETE operations on component child rows when their
-- owning component is already published.
--
-- PARENT RESOLUTION STRATEGY
-- --------------------------
-- 1) dyno_form.component_panel
--    - child row contains component_id directly
--    - lookup: component(tenant_id, id) = (OLD.tenant_id, OLD.component_id)
--
-- 2) dyno_form.component_panel_field
--    - child row contains panel_id
--    - resolve component via component_panel then join to component
--
-- SAFETY GUARDRAIL
-- ---------------
-- If this function is attached to an unsupported table name, it raises an
-- exception. This avoids silent misconfiguration that could weaken the
-- immutability policy.
--
-- ----------------------------------------------------------------------

CREATE OR REPLACE FUNCTION dyno_form.block_writes_when_parent_component_published()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
  parent_published boolean;
BEGIN
  -- Resolve parent component publish state based on triggering table.
  IF TG_TABLE_NAME = 'component_panel' THEN
    SELECT c.is_published
      INTO parent_published
      FROM dyno_form.component c
     WHERE c.tenant_id = OLD.tenant_id
       AND c.id = OLD.component_id;

  ELSIF TG_TABLE_NAME = 'component_panel_field' THEN
    SELECT c.is_published
      INTO parent_published
      FROM dyno_form.component_panel p
      JOIN dyno_form.component c
        ON c.tenant_id = p.tenant_id
       AND c.id = p.component_id
     WHERE p.tenant_id = OLD.tenant_id
       AND p.id = OLD.panel_id;

  ELSE
    -- Misconfiguration guardrail: do not silently allow writes.
    RAISE EXCEPTION 'Trigger function % attached to unsupported table %.%',
      'dyno_form.block_writes_when_parent_component_published()',
      TG_TABLE_SCHEMA,
      TG_TABLE_NAME
      USING ERRCODE = 'invalid_parameter_value';
  END IF;

  -- Enforce immutability if the parent component is published.
  IF parent_published IS TRUE THEN
    RAISE EXCEPTION '% is not allowed: parent component is published.', TG_OP
      USING
        ERRCODE = 'check_violation',
        DETAIL  = format(
                    'Operation=%s Table=%I.%I parent component is published',
                    TG_OP,
                    TG_TABLE_SCHEMA,
                    TG_TABLE_NAME
                  ),
        HINT    = 'Clone the component (or edit an unpublished draft) before modifying or deleting its panels or fields.';
  END IF;

  -- Allow UPDATE to proceed by returning NEW.
  IF TG_OP = 'UPDATE' THEN
    RETURN NEW;
  END IF;

  -- Allow DELETE to proceed by returning OLD.
  RETURN OLD;
END;
$$;


COMMENT ON FUNCTION dyno_form.block_writes_when_parent_component_published() IS
'Trigger function that enforces immutability of component structure rows when the owning parent component is published. Used as a BEFORE UPDATE/DELETE trigger on component child tables (e.g., component_panel, component_panel_field). Resolves parent publish state using tenant-safe joins (either directly via component_id or indirectly via panel_id -> component_panel -> component). If the parent component is published, blocks the write with check_violation. Includes a guardrail that raises invalid_parameter_value if attached to an unsupported table to prevent silent misconfiguration.';


-- ----------------------------------------------------------------------
-- Trigger attachments (component structure children)
-- ----------------------------------------------------------------------
--
-- Each table receives:
--   - BEFORE UPDATE trigger
--   - BEFORE DELETE trigger
--
-- ----------------------------------------------------------------------

-- dyno_form.component_panel
CREATE TRIGGER tr_block_writes_when_parent_component_published
BEFORE UPDATE ON dyno_form.component_panel
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_parent_component_published();

CREATE TRIGGER tr_block_deletes_when_parent_component_published
BEFORE DELETE ON dyno_form.component_panel
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_parent_component_published();

-- dyno_form.component_panel_field
CREATE TRIGGER tr_block_writes_when_parent_component_published
BEFORE UPDATE ON dyno_form.component_panel_field
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_parent_component_published();

CREATE TRIGGER tr_block_deletes_when_parent_component_published
BEFORE DELETE ON dyno_form.component_panel_field
FOR EACH ROW
EXECUTE FUNCTION dyno_form.block_writes_when_parent_component_published();


-- ======================================================================
-- End of updated schema
-- ======================================================================
