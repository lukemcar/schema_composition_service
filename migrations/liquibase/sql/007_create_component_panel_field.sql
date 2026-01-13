-- liquibase formatted sql
-- changeset formless_agent:007_create_component_panel_field runOnChange:true splitStatements:false

CREATE TABLE IF NOT EXISTS component_panel_field (
    component_panel_field_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    component_panel_id UUID NOT NULL,
    field_def_id UUID NOT NULL,
    overrides JSONB,
    field_order INTEGER NOT NULL DEFAULT 0,
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS ix_component_panel_field_panel
    ON component_panel_field (component_panel_id, field_order);