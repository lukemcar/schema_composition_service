-- liquibase formatted sql
-- changeset formless_agent:005_create_component runOnChange:true splitStatements:false

CREATE TABLE IF NOT EXISTS component (
    component_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    component_key VARCHAR(200) NOT NULL,
    version VARCHAR(50) NOT NULL,
    component_name VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    category_id UUID,
    ui_config JSONB,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    CONSTRAINT uq_component_tenant_key_version UNIQUE (tenant_id, component_key, version)
);

-- index to query active components per tenant
CREATE INDEX IF NOT EXISTS ix_component_tenant_active
    ON component (tenant_id, is_active);