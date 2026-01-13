-- ======================================================================
-- MyEntity Service – Initial Schema
-- ======================================================================
-- liquibase formatted sql
-- changeset my_entity_service:001_create_my_entity

SET search_path TO public;

-- ----------------------------------------------------------------------
-- 1. my_entity
-- ----------------------------------------------------------------------
CREATE TABLE my_entity (
    my_entity_id UUID PRIMARY KEY,
    tenant_id     UUID       NOT NULL,
    name          VARCHAR(255) NOT NULL,
    data          JSONB,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by    VARCHAR(100),
    updated_by    VARCHAR(100)
);

-- Index to support tenant‑scoped queries
CREATE INDEX idx_my_entity_tenant ON my_entity (tenant_id);

-- Optional uniqueness constraint can be added here (e.g., tenant_id, name)
-- CREATE UNIQUE INDEX ux_my_entity_tenant_name ON my_entity (tenant_id, name);