"""
Service layer for health checks.
"""

import logging

from fastapi import HTTPException, status

from app.core.db import check_database_connection
from app.domain.schemas.health import HealthResponse


logger = logging.getLogger("my_entity_service.health_service")


def get_liveness() -> HealthResponse:
    """Return a basic liveness probe.

    The ``service`` detail allows callers to identify the service
    responding to the probe.  Adjust this string when copying the
    pattern to a new service.
    """
    return HealthResponse(status="ok", details={"service": "my-entity-service"})


def get_readiness() -> HealthResponse:
    try:
        check_database_connection()
    except Exception as exc:
        logger.warning("Database not ready", exc_info=exc)
        response = HealthResponse(status="degraded", details={"database": "unavailable"})
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=response.dict())
    return HealthResponse(status="ok", details={"database": "ready"})
