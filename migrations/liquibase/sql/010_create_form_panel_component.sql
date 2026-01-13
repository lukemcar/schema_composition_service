-- liquibase formatted sql
-- changeset formless_agent:010_create_form_panel_component runOnChange:true splitStatements:false

CREATE TABLE IF NOT EXISTS form_panel_component (
    form_panel_component_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    form_panel_id UUID NOT NULL,
    component_id UUID NOT NULL,
    config JSONB,
    component_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS ix_form_panel_component_panel
    ON form_panel_component (form_panel_id, component_order);