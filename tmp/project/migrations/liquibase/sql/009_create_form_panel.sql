-- liquibase formatted sql
-- changeset formless_agent:009_create_form_panel runOnChange:true splitStatements:false

CREATE TABLE IF NOT EXISTS form_panel (
    form_panel_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    form_id UUID NOT NULL,
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

CREATE INDEX IF NOT EXISTS ix_form_panel_form
    ON form_panel (form_id, panel_order);