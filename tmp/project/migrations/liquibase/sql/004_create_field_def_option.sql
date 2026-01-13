-- liquibase formatted sql
-- changeset crm_service:004_create_field_def_option

--
-- Create table: field_def_option
--
-- This table stores allowed options for SELECT and MULTISELECT fields.  Each
-- option is scoped to a tenant and a specific field definition.  A UUID
-- primary key is used instead of the composite primary key defined in the
-- original schema.  Uniqueness constraints enforce that option keys and
-- orders are unique per (tenant_id, field_def_id).

CREATE TABLE IF NOT EXISTS field_def_option (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    field_def_id UUID NOT NULL,
    option_key VARCHAR(200) NOT NULL,
    option_label VARCHAR(400) NOT NULL,
    option_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),

    CONSTRAINT uq_field_def_option_tenant_field_key
        UNIQUE (tenant_id, field_def_id, option_key),

    CONSTRAINT uq_field_def_option_tenant_field_order
        UNIQUE (tenant_id, field_def_id, option_order),

    -- Ensure option_order is non-negative
    CONSTRAINT ck_field_def_option_order_non_negative
        CHECK (option_order >= 0),

    -- Tenant-safe FK to field_def (optional enforcement at application layer)
    -- FOREIGN KEY (tenant_id, field_def_id)
    --     REFERENCES field_def (tenant_id, id)
    --     ON DELETE CASCADE
    -- DEFERRABLE INITIALLY DEFERRED
    
    -- Prevent blank/whitespace keys and labels
    CONSTRAINT chk_field_def_option_key_not_blank
        CHECK (length(btrim(option_key)) > 0),
    CONSTRAINT chk_field_def_option_label_not_blank
        CHECK (length(btrim(option_label)) > 0)
);

-- Index to fetch options ordered by option_order
CREATE INDEX IF NOT EXISTS ix_field_def_option_tenant_field_order
    ON field_def_option (tenant_id, field_def_id, option_order);