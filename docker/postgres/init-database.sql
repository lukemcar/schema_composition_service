-- Create the main database for the MyEntity service
CREATE DATABASE my_entity_service;

\c my_entity_service;


-- API user (FastAPI service)
CREATE USER my_entity_app WITH PASSWORD 'my_entity_app_password';

-- Admin user (Liquibase + DB migrations)
CREATE USER my_entity_admin WITH PASSWORD 'my_entity_admin_password';

-- Worker user (Celery or async background jobs)
CREATE USER my_entity_worker WITH PASSWORD 'my_entity_worker_password';

CREATE SCHEMA IF NOT EXISTS public AUTHORIZATION my_entity_admin;


GRANT ALL PRIVILEGES ON DATABASE my_entity_service TO my_entity_admin;
GRANT ALL PRIVILEGES ON SCHEMA public TO my_entity_admin;

GRANT USAGE, CREATE ON SCHEMA public TO my_entity_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO my_entity_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE ON SEQUENCES TO my_entity_app;

GRANT USAGE ON SCHEMA public TO my_entity_worker;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE ON TABLES TO my_entity_worker;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE ON SEQUENCES TO my_entity_worker;

-- =========
