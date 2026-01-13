"""
Centralised exception handlers for Dyno Conversa API.

This module registers exception handlers on a FastAPI application to
ensure all errors are returned in a consistent format using the
``ErrorResponseBody`` schema.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.domain.schemas.common import ErrorResponseBody

logger = logging.getLogger(__name__)


def add_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers on the given FastAPI app."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        logger.error("HTTP error: %s", exc.detail)
        # The detail may be a string or dict; convert to message
        message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
        # Ensure code is a string; exc.status_code is an int but our schema expects a string
        # Fall back to the HTTP status code if no custom code is provided
        status_code = getattr(exc, "code", exc.status_code)
        error_body = ErrorResponseBody(code=str(status_code), message=message)
        return JSONResponse(status_code=exc.status_code, content=error_body.model_dump())

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
        logger.error("Validation error: %s", exc.errors())
        error_body = ErrorResponseBody(code="VALIDATION_ERROR", message="Invalid request parameters")
        return JSONResponse(status_code=422, content=error_body.model_dump())

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error: %s", exc)
        # Hide internal error details from clients
        error_body = ErrorResponseBody(code="INTERNAL_ERROR", message="An unexpected error occurred")
        return JSONResponse(status_code=500, content=error_body.model_dump())