-- liquibase formatted sql
-- changeset formless_agent:012_create_form_submission runOnChange:true splitStatements:false

CREATE TABLE IF NOT EXISTS form_submission (
    form_submission_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    form_id UUID NOT NULL,
    submission_status VARCHAR(50) NOT NULL DEFAULT 'draft',
    submitted_at TIMESTAMP,
    submitted_by VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS ix_form_submission_form
    ON form_submission (form_id, submission_status);