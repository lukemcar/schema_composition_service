-- liquibase formatted sql
-- changeset formless_agent:011_create_form_panel_field runOnChange:true splitStatements:false

CREATE TABLE IF NOT EXISTS form_panel_field (
    form_panel_field_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    form_panel_id UUID NOT NULL,
    field_def_id UUID NOT NULL,
    overrides JSONB,
    field_order INTEGER NOT NULL DEFAULT 0,
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS ix_form_panel_field_panel
    ON form_panel_field (form_panel_id, field_order);