SET search_path TO public, schema_composition;

-- Create the main database for the SchemaComposition service
CREATE DATABASE schema_composition_db;

\c schema_composition_db;

-- ==============================================
-- Enable extensions
-- ==============================================

CREATE EXTENSION IF NOT EXISTS pg_jsonschema;


-- API user (FastAPI service)
CREATE USER schema_composition_app WITH PASSWORD 'schema_composition_app_password';

-- Admin user (Liquibase + DB migrations)
CREATE USER schema_composition_admin WITH PASSWORD 'schema_composition_admin_password';

-- Worker user (Celery or async background jobs)
CREATE USER schema_composition_worker WITH PASSWORD 'schema_composition_worker_password';

CREATE SCHEMA IF NOT EXISTS schema_composition AUTHORIZATION schema_composition_admin;


GRANT ALL PRIVILEGES ON DATABASE schema_composition_db TO schema_composition_admin;
GRANT ALL PRIVILEGES ON SCHEMA schema_composition TO schema_composition_admin;

GRANT USAGE, CREATE ON SCHEMA schema_composition TO schema_composition_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_composition
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO schema_composition_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_composition
  GRANT USAGE ON SEQUENCES TO schema_composition_app;

GRANT USAGE ON SCHEMA schema_composition TO schema_composition_worker;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_composition
  GRANT SELECT, INSERT, UPDATE ON TABLES TO schema_composition_worker;
ALTER DEFAULT PRIVILEGES IN SCHEMA schema_composition
  GRANT USAGE ON SEQUENCES TO schema_composition_worker;

GRANT USAGE ON SCHEMA public TO schema_composition_admin;
GRANT USAGE ON SCHEMA public TO schema_composition_app;
GRANT USAGE ON SCHEMA public TO schema_composition_worker;


-- =========
