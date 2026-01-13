-- liquibase formatted sql
-- changeset formless_agent:013_create_form_submission_value runOnChange:true splitStatements:false

CREATE TABLE IF NOT EXISTS form_submission_value (
    form_submission_value_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    form_submission_id UUID NOT NULL,
    field_instance_path VARCHAR(255) NOT NULL,
    value JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS ix_form_submission_value_submission
    ON form_submission_value (form_submission_id);