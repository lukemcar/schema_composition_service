# Schema Composition Service

The **Schema Composition Service** is a multitenant backend for defining, composing and executing dynamic forms and user‑interface components.  It provides a RESTful API built with **FastAPI** to create and manage form definitions, reusable components, panels, fields, options and end‑user submissions.  Each domain concept is implemented using a domain‑driven design: entities describe the core business objects, models map those objects to relational tables via SQLAlchemy, repositories encapsulate data‑access logic, services implement business rules and coordinate messaging, and API routes expose CRUD operations for each resource.  A Celery worker and a message bus complete the architecture by publishing domain events and executing asynchronous tasks.

The project is organised as a Python package with clearly separated layers and extensive support tooling (Docker Compose, Liquibase migrations, a Makefile and tests) to streamline development and deployment.  This README documents the purpose of each directory, how to install and run the service, the available Makefile commands and how to contribute.

## Project Structure

```
schema_composition_service_python/
├── app/                 # Application layer with API routes, configuration, messaging and utilities
├── docker/              # Dockerfiles and entrypoint scripts for the API and worker containers
├── liquibase/           # Database changelog and SQL migration files managed by Liquibase
├── schema_composition_service/  # Domain layer with entities, models, repositories, services and schemas
├── tests/               # Unit and integration tests
├── docker-compose.yml   # Composition of PostgreSQL, Redis, API and worker services for development
├── Makefile             # Build, install, test and environment management commands
├── main_api.py          # FastAPI entrypoint used by the API container
├── main_worker.py       # Celery worker entrypoint used by the worker container
├── pyproject.toml       # Poetry configuration specifying dependencies and package metadata
└── .env.example         # Example environment variables for local development
```

### Top‑Level Files

* **`main_api.py`** – Creates a `FastAPI` application, registers all routers under the tenant‑scoped prefixes (e.g. `/tenants/{tenant_id}/forms`) and configures the OpenAPI documentation.  When run, it reads settings from environment variables via `app.core.config.Settings` and calls `create_application()` to build the app.

* **`main_worker.py`** – Entry point for the Celery worker.  It initialises the Celery application using settings in `app.core.config.Settings`, registers task modules and instructs Celery to discover tasks defined under `app.messaging.tasks`.  This worker processes events published by the API and executes asynchronous operations such as sending messages to other services.

* **`docker-compose.yml`** – Defines a development stack with four services:
  * **db** – a PostgreSQL container seeded by Liquibase migrations.
  * **redis** – a Redis instance used by Celery as a result backend and cache.
  * **api** – runs `main_api.py` on port `8001` and exposes the REST API.
  * **worker** – runs `main_worker.py` and listens to message queues defined in `app.core.config`.
  Environment variables can be supplied via a `.env` file; a sample configuration is provided in `.env.example`.

* **`Makefile`** – A convenience wrapper around common tasks.  Notable targets include:

  | Target                 | Description                                                                                          |
  |------------------------|------------------------------------------------------------------------------------------------------|
  | **`install`**          | Installs the service and all required dependencies into the current Python environment.               |
  | **`install-dev`**      | Installs development dependencies (`poetry install --with dev`).                                     |
  | **`compile`**          | Runs `python -m compileall` to byte‑compile the source tree into `__pycache__`.                      |
  | **`venv-clean`**       | Removes the `venv` directory and reinstalls dependencies.                                             |
  | **`test`**             | Runs all tests using `pytest -q`.                                                                    |
  | **`test-unit`**        | Runs unit tests only (skips integration tests that require a database).                                |
  | **`test-integration`** | Runs integration tests that rely on a running PostgreSQL instance.                                    |
  | **`up`**               | Builds and starts the Docker Compose development environment.                                         |
  | **`down`**             | Stops the Compose environment but retains volumes for reuse.                                          |
  | **`destroy`**          | Stops and removes the Compose environment, including volumes and networks.                            |
  | **`clean`**            | Runs `docker system prune` to remove stopped containers, unused networks and dangling images.         |
  | **`zip` / `unzip`**    | Packages or unpacks the source code into a ZIP archive for distribution.                              |

* **`pyproject.toml`** – Configures the project for Poetry, including Python requirements (`fastapi`, `sqlalchemy`, `pydantic`, `celery`, `aio_pika`, etc.), development tools (`pytest`, `black`, `ruff`, `bandit`) and metadata.  It also defines optional groups for development (`dev`) and for AI features (the `ai` group).

* **`.env.example`** – A template of the environment variables consumed by the application.  Copy this file to `.env` and customise values for database credentials, Redis connection, JWT secret, message‑broker settings and optional OpenAI keys.

## Application Layer (`app/`)

The `app` package contains the FastAPI application and supporting infrastructure.  Its subpackages are organised by concern:

### `app/api`

Defines all HTTP endpoints.  The `routes` package contains a module for each domain resource (e.g. `component_routes.py`, `field_def_routes.py`, `form_routes.py`, etc.).  Every route module declares a FastAPI router with CRUD endpoints under `/tenants/{tenant_id}/<resource>`, performs request validation using Pydantic schemas from the domain layer and delegates to service functions.  The `main.py` file inside `app/api` composes these routers into the FastAPI application.  Dependency injection is performed via `app/api/dependencies.py` which provides functions for database sessions, caching, messaging and pagination parameters.

### `app/core`

Holds cross‑cutting configuration and helpers:

* **`config.py`** – Defines a `Settings` Pydantic model that reads environment variables and centralises configuration for the database, Redis, JWT secrets, Celery, message broker and OpenAI credentials.
* **`db.py`** – Sets up SQLAlchemy’s `AsyncSession`, provides `get_session` dependency injection and initialises the database engine using the configured DSN.  Models are imported in `app/domain/models/__init__.py` to ensure they are registered with the metadata.
* **`cache.py`** – Creates a Redis client for caching and stores it in the FastAPI application state.
* **`messaging.py`** – Configures the message bus using `aio_pika`.  It declares exchanges and queues, establishes channels and exposes a `publish_message` function for producers.
* **`logging.py`** – Configures structured logging with coloured output and correlation IDs.  Provides a `get_logger` helper used throughout the service.

### `app/messaging`

Implements the asynchronous messaging layer.  It defines:

* **`schemas`** – Pydantic classes representing messages for each domain event (`created`, `updated` and `deleted`).  These are serialised to JSON before publishing.
* **`producers`** – Functions that publish domain events to the message bus.  Each producer sends messages with routing keys like `SchemaComposition.<Domain>.<Event>`.
* **`tasks`** – Celery task modules imported by the worker.  Tasks typically call service functions and publish events or send notifications.
* **`setup.py`** – A helper that declares the exchanges, queues and routing keys for all domains when the application starts.

### `app/ai`

Contains optional AI integration.  The `llm_client.py` module wraps calls to a large language model (such as OpenAI’s GPT) using API keys from configuration.  The `agents` package defines chat agents that can propose new field definitions or analyse form structures.  These features are not enabled by default; they require the optional AI dependencies (`poetry install --with ai`) and an `OPENAI_API_KEY` environment variable.

### `app/util`

Provides miscellaneous helpers including:

* `kebab.py` – Converts strings to kebab‑case for generating business keys.
* `logger.py` – Returns a configured logger bound to a module name.
* `pagination.py` – Implements common pagination logic used by API routes.
* `schemas.py` – Base classes for API response envelopes with metadata such as `total`, `limit` and `offset`.

## Domain Layer (`schema_composition_service/`)

The `schema_composition_service` package embodies the business logic.  It follows a clean architecture: entities capture the core concepts, models map those concepts to tables, repositories handle persistence, services implement use‑cases and publish events, and schemas define request/response shapes.

### Entities

Modules under `domain/entities/` define dataclasses for each concept:

* `form_catalog_category.py` – Describes categories used to group field definitions and components.
* `field_def.py` – Represents the definition of a field, including its data type, element type and validation rules.
* `field_def_option.py` – Stores selectable options for single‑ and multi‑select fields.
* `component.py` – Represents a reusable UI component.
* `component_panel.py`, `component_panel_field.py` – Describe panels inside a component and the placement of fields on those panels.
* `form.py` – Represents the top‑level form definition.
* `form_panel.py`, `form_panel_component.py`, `form_panel_field.py` – Describe panels within a form and the placement of components and fields.
* `form_submission.py` – Captures metadata about a user’s submission (draft vs submitted, version, archived flags).
* `form_submission_value.py` – Stores individual field values captured in a submission, keyed by a fully qualified path.

### Enums

The `domain/enums/` package centralises common enumerations.  For example, `field_data_type.py` defines allowed data shapes (`TEXT`, `NUMBER`, `BOOLEAN`, `DATE`, `DATETIME`, `SINGLESELECT`, `MULTISELECT`), `field_element_type.py` describes UI controls (`TEXT`, `TEXTAREA`, `SELECT`, etc.), and `artifact_source_type.py` identifies the origin of catalog artefacts (`MARKETPLACE`, `PROVIDER`, `TENANT`, `SYSTEM`).

### Models

SQLAlchemy models live in `domain/models/`.  Each file maps a domain entity to a database table with tenant‑scoped primary keys, business keys, flags (e.g. `is_active`, `is_archived`) and audit columns (`created_at`, `updated_at`).  Relationships are defined via foreign keys and SQLAlchemy `relationship()` declarations.  Models are imported into `domain/models/__init__.py` so that they are registered with the SQLAlchemy metadata for Alembic and Liquibase.

### Schemas

The `domain/schemas/` package defines Pydantic models used by the API for input validation and output formatting.  Each domain has `Create`, `Update`, `Out` (output) and `ListResponse` schemas.  These schemas include metadata such as `total`, `limit` and `offset` for paginated responses and follow a consistent naming scheme.

### Repositories

Classes in `domain/repositories/` encapsulate CRUD operations on the models.  Each repository uses the asynchronous SQLAlchemy session provided by the application layer and exposes methods like `create`, `get`, `update` and `delete`.  Repositories hide the persistence details from the services.

### Services

Service modules in `domain/services/` implement business logic by coordinating repositories and messaging.  For instance, the `form_service.py` module provides `create_form`, `update_form`, `get_form` and `delete_form` functions.  After performing persistence operations, services publish a corresponding `created`, `updated` or `deleted` event through the appropriate producer in `app.messaging.producers`.  Services are exposed via `schema_composition_service/domain/services/__init__.py` to simplify imports in the API layer.

### Errors

Custom exception classes reside in `domain/errors/`.  They capture domain‑specific error conditions such as `EntityNotFoundError` and `DuplicateKeyError` and are translated into HTTP error responses by the API layer.

## Database Migrations (`liquibase/`)

Database schema changes are managed with **Liquibase**.  The `changelog-root.xml` aggregates individual SQL files located in `liquibase/changelog` (e.g. `004_create_field_def_option.sql` through `013_create_form_submission_value.sql`) to create and update tables.  Each migration corresponds to the domain entities described above and includes primary keys, unique constraints, foreign keys, indexes and audit columns.  When the `db` container starts, Liquibase automatically applies these migrations to the PostgreSQL instance.

## Docker Setup (`docker/`)

The `docker/` directory contains Dockerfiles and startup scripts used by the Compose stack:

* **`api/Dockerfile`** – Builds the API image.  It installs Poetry, copies the source code and dependencies, compiles the project, and sets the entrypoint to run `python main_api.py`.
* **`api/start.sh`** – Waits for the PostgreSQL and RabbitMQ services to be ready, then launches the FastAPI application with `uvicorn` on host `0.0.0.0` and port `8001`.
* **`worker/Dockerfile`** – Builds the Celery worker image.  It installs dependencies, copies the project and configures Celery to run tasks defined in `app/messaging/tasks`.  The entrypoint is `celery -A main_worker.celery_app worker`.
* **`wait-for-it.sh`** – A utility script used by the API and worker images to pause execution until dependent services are reachable.

## Tests (`tests/`)

The `tests/` package contains unit and integration tests.  Unit tests focus on service functions and repositories and can be run in isolation (`make test-unit`).  Integration tests under `tests/api` spin up a temporary database and verify that the API routes return the expected responses (`make test-integration`).  All tests can be run with `make test`.

## Installation & Development

### Prerequisites

* Python 3.11
* Docker and Docker Compose
* [Poetry](https://python-poetry.org/) for dependency management (optional if using Docker only)

### Local Setup (without Docker)

1. Clone the repository and create a virtual environment:

   ```bash
   git clone <repo-url>
   cd schema_composition_service_python
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies using the Makefile:

   ```bash
   make install            # installs required dependencies
   make install-dev        # installs development and optional AI dependencies
   ```

3. Copy the example environment file and adjust credentials:

   ```bash
   cp .env.example .env
   # edit .env with your PostgreSQL, Redis, JWT and message‑broker settings
   ```

4. Start a local PostgreSQL and Redis instance (e.g. via Docker Compose):

   ```bash
   docker compose --env-file .env up -d db redis
   ```

5. Apply database migrations with Liquibase (automatically done when using Docker Compose).  Alternatively you can run the `liquibase` CLI against `liquibase/changelog-root.xml`.

6. Run the API server:

   ```bash
   uvicorn main_api:app --host 0.0.0.0 --port 8001 --reload
   ```

7. Run the Celery worker in a separate terminal:

   ```bash
   celery -A main_worker.celery_app worker --loglevel=info
   ```

8. Navigate to `http://localhost:8001/docs` to explore the automatically generated OpenAPI documentation.

### Running with Docker Compose

For a turnkey development environment, use the included Compose file.  Copy `.env.example` to `.env.dev`, adjust the variables as needed and then run:

```bash
make up

# Or, manually:
docker compose --env-file .env.dev up --build
```

The API will listen on port `8001` and the worker will consume messages in the background.  Use `make down` to stop the stack while preserving data volumes, or `make destroy` to remove everything.

## Running Tests

* **Unit tests** – `make test-unit` runs fast tests that do not require an external database or message broker.  These tests mock the database session and verify service logic.
* **Integration tests** – `make test-integration` runs tests that require a PostgreSQL instance and exercise the API routes.  Ensure the `db` service is running (e.g. via `make up`) before running these tests.
* **All tests** – `make test` runs both unit and integration tests.

## Extending the Service

New domain concepts can be added by following the existing pattern:

1. Create an entity dataclass under `schema_composition_service/domain/entities` to represent the core fields.
2. Create a SQLAlchemy model under `domain/models` that maps the entity to a table.  Define tenant‑scoped primary keys, business keys and audit columns.
3. Add Pydantic schemas under `domain/schemas` for create, update, output and list responses.
4. Implement a repository class under `domain/repositories` for persistence.
5. Implement service functions under `domain/services` that use the repository and publish events via `app.messaging.producers`.
6. Add API routes under `app/api/routes` that depend on the service functions.
7. Add a Liquibase change file under `liquibase/changelog` and include it in `changelog-root.xml`.
