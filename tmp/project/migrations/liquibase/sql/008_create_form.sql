-- liquibase formatted sql
-- changeset formless_agent:008_create_form runOnChange:true splitStatements:false

CREATE TABLE IF NOT EXISTS form (
    form_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    form_key VARCHAR(200) NOT NULL,
    version VARCHAR(50) NOT NULL,
    form_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    category_id UUID,
    ui_config JSONB,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    CONSTRAINT uq_form_tenant_key_version UNIQUE (tenant_id, form_key, version)
);

CREATE INDEX IF NOT EXISTS ix_form_tenant_active
    ON form (tenant_id, is_active);