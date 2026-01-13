-- liquibase formatted sql
-- changeset crm_service:002_create_form_catalog_category

--
-- Create table: form_catalog_category
--
-- This table organizes reusable form elements (field definitions and
-- components) into categories. Each category is scoped to a tenant and
-- identified by a unique key per tenant. A UUID primary key is used
-- instead of the surrogate key defined in the original schema. Audit
-- columns record creation and update metadata.

CREATE TABLE IF NOT EXISTS form_catalog_category (
    form_catalog_category_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    category_key VARCHAR(100) NOT NULL,
    category_name VARCHAR(255),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    CONSTRAINT uq_form_catalog_category_tenant_key
        UNIQUE (tenant_id, category_key)
);

-- Index on tenant_id for efficient scoping
CREATE INDEX IF NOT EXISTS ix_form_catalog_category_tenant
    ON form_catalog_category (tenant_id);