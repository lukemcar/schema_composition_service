"""
Entry point for the SchemaComposition Service API.

This module wires together the FastAPI application, telemetry
instrumentation and Liquibase migrations.  Only the health and
SchemaComposition routes are mounted here.  When adding additional domains
to your service, follow the pattern used here by importing the
router from your new ``app.api.routes.<your_domain>`` module and
including it on the FastAPI app via ``app.include_router(...)``.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.core.config import Config
from app.core.logging import configure_logging
from app.core.telemetry import init_tracing, instrument_fastapi, instrument_httpx
from app.api.error_handlers import add_exception_handlers
from app.util.liquibase import apply_changelog
from app.api.routes.health import router as health_router

from app.api.routes.form_catalog_category import (
    router as form_catalog_category_router,
)  # type: ignore
from app.api.routes.field_def import router as field_def_router  # type: ignore
from app.api.routes.field_def_option import (
    router as field_def_option_router,
)  # type: ignore
from app.api.routes.component import router as component_router  # type: ignore
from app.api.routes.component_panel import (
    router as component_panel_router,
)  # type: ignore
from app.api.routes.component_panel_field import (
    router as component_panel_field_router,
)  # type: ignore
from app.api.routes.form import router as form_router  # type: ignore
from app.api.routes.form_panel import router as form_panel_router  # type: ignore
from app.api.routes.form_panel_component import (
    router as form_panel_component_router,
)  # type: ignore
from app.api.routes.form_panel_field import (
    router as form_panel_field_router,
)  # type: ignore
from app.api.routes.form_submission import router as form_submission_router  # type: ignore
from app.api.routes.form_submission_value import (
    router as form_submission_value_router,
)  # type: ignore

# Configure logging and tracing at import time.  This ensures any log
# messages emitted during module import are formatted consistently and
# include trace context if available.
logger = configure_logging()
init_tracing(service_name="schema-composition-service.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup/shutdown hook for the FastAPI application.

    On startup this will apply any pending Liquibase migrations (if
    enabled via the ``LIQUIBASE_ENABLED`` environment variable).  On
    shutdown it simply logs a message indicating the service is
    stopping.  Extend this function to perform additional startup or
    teardown tasks as needed.
    """
    logger.info("startup_event: SchemaComposition Service is starting")
    if Config.liquibase_enabled():
        try:
            apply_changelog(Config.liquibase_property_file())
        except Exception as exc:
            logger.error(
                "An error occurred while applying Liquibase changelog", exc_info=exc
            )
    else:
        logger.info("Skipping Liquibase schema validation and update")
    yield
    logger.info("shutdown_event: SchemaComposition Service is shutting down")


# Create the FastAPI application and configure OpenAPI metadata.  When
# adding new domains adjust the service name and version appropriately.
app = FastAPI(lifespan=lifespan, title="SchemaComposition Service", version="0.1.0")

# Instrument FastAPI and httpx for distributed tracing.  If
# OpenTelemetry is not installed these calls are no‑ops.
instrument_fastapi(app)
instrument_httpx()

# Register global exception handlers (e.g. to convert HTTPException
# objects into structured JSON responses).
add_exception_handlers(app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Simple logging middleware to record incoming requests."""
    ip_address = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path
    logger.info("Host %s accessed %s with %s", ip_address, path, method)
    response = await call_next(request)
    return response


# Mount routers.  Each router encapsulates a set of related routes
# (endpoints) for a single resource.  When adding new domains import
# your router here and include it on the app.
app.include_router(health_router)
app.include_router(form_catalog_category_router)
app.include_router(field_def_router)
app.include_router(field_def_option_router)
app.include_router(component_router)
app.include_router(component_panel_router)
app.include_router(component_panel_field_router)
app.include_router(form_router)
app.include_router(form_panel_router)
app.include_router(form_panel_component_router)
app.include_router(form_panel_field_router)
app.include_router(form_submission_router)
app.include_router(form_submission_value_router)