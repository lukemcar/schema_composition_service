-- liquibase formatted sql
-- changeset crm_service:003_create_field_def

--
-- Create table: field_def
--
-- This table stores reusable field definitions for a tenant. Each
-- definition describes the data semantics, UI rendering, and other
-- metadata. A UUID primary key is used instead of the composite key
-- from the original schema. Composite uniqueness constraints enforce
-- uniqueness on the business key (field_key + version) per tenant.

CREATE TABLE IF NOT EXISTS field_def (
    field_def_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    field_key VARCHAR(100) NOT NULL,
    field_version INTEGER NOT NULL DEFAULT 1,
    field_name VARCHAR(255) NOT NULL,
    field_label VARCHAR(255),
    data_type VARCHAR(50) NOT NULL,
    element_type VARCHAR(50) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    ui_config JSONB,
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    is_searchable BOOLEAN NOT NULL DEFAULT FALSE,
    is_display_field BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT uq_field_def_tenant_key_version
        UNIQUE (tenant_id, field_key, field_version)
);

-- Index on tenant_id for efficient scoping
CREATE INDEX IF NOT EXISTS ix_field_def_tenant
    ON field_def (tenant_id);