-- liquibase formatted sql
-- changeset formless_agent:006_create_component_panel runOnChange:true splitStatements:false

CREATE TABLE IF NOT EXISTS component_panel (
    component_panel_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    component_id UUID NOT NULL,
    parent_panel_id UUID,
    panel_key VARCHAR(200) NOT NULL,
    panel_label VARCHAR(100),
    ui_config JSONB,
    panel_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS ix_component_panel_component
    ON component_panel (component_id, panel_order);