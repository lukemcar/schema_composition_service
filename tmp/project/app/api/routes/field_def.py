"""
FastAPI routes for the FieldDef resource.

This module defines a REST API for creating, retrieving, listing,
updating and deleting FieldDef instances.  All operations are
tenant‑scoped: the tenant identifier must be provided as a path
parameter and the JWT token presented by the caller must include a
matching ``tenant_id`` claim.  When adding a new domain object copy
this file and adjust the router prefix, schemas and service calls
accordingly.
"""

from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.util.jwt_util import auth_jwt
from app.domain.schemas import (
    FieldDefCreate,
    FieldDefUpdate,
    FieldDefOut,
    FieldDefListResponse,
)
from app.domain.services import field_def_service as service


# ---------------------------------------------------------------------------
# Router configuration
#
# The prefix embeds the tenant identifier in the URL path.  All routes in
# this router operate on resources owned by a single tenant.  The
# ``tags`` argument groups the endpoints in the generated OpenAPI
# documentation.
router = APIRouter(
    prefix="/tenants/{tenant_id}/field-defs",
    tags=["field-defs"],
)


@router.get(
    "/",
    response_model=FieldDefListResponse,
)
def list_field_defs(
    *,
    tenant_id: uuid.UUID,
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of items to return.",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of items to skip before starting to collect the result set.",
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FieldDefListResponse:
    """Retrieve a paginated list of FieldDef records for a tenant.

    This endpoint returns a paginated collection of FieldDef objects.
    The caller must supply a valid JWT token with a ``tenant_id`` claim
    matching the path parameter.  Optional ``limit`` and ``offset``
    query parameters control pagination.
    """
    items, total = service.list_field_defs(
        db=db,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )
    return FieldDefListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/",
    response_model=FieldDefOut,
    status_code=status.HTTP_201_CREATED,
)
def create_field_def(
    *,
    tenant_id: uuid.UUID,
    field_def_in: FieldDefCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FieldDefOut:
    """Create a new FieldDef for the specified tenant.

    The ``tenant_id`` is derived from the path and validated against the
    JWT via the ``auth_jwt`` dependency.  The ``created_by`` user is
    inferred from the JWT ``sub`` claim if present, falling back to
    "system" otherwise.
    """
    created_by = current_user.get("sub", "system")
    entity = service.create_field_def(
        db=db,
        tenant_id=tenant_id,
        data=field_def_in,
        created_by=created_by,
    )
    return entity


@router.get(
    "/{field_def_id}",
    response_model=FieldDefOut,
)
def get_field_def(
    *,
    tenant_id: uuid.UUID,
    field_def_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FieldDefOut:
    """Retrieve a single FieldDef by its identifier for the given tenant."""
    return service.get_field_def(
        db=db,
        tenant_id=tenant_id,
        field_def_id=field_def_id,
    )


@router.put(
    "/{field_def_id}",
    response_model=FieldDefOut,
)
def update_field_def(
    *,
    tenant_id: uuid.UUID,
    field_def_id: uuid.UUID,
    field_def_in: FieldDefUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FieldDefOut:
    """
    Replace a FieldDef record with the provided fields.

    Only fields provided in the request body are updated.  The
    ``modified_by`` user is taken from the JWT ``sub`` claim if
    available.
    """
    modified_by = current_user.get("sub", "system")
    entity = service.update_field_def(
        db=db,
        tenant_id=tenant_id,
        field_def_id=field_def_id,
        data=field_def_in,
        modified_by=modified_by,
    )
    return entity


@router.delete(
    "/{field_def_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_field_def(
    *,
    tenant_id: uuid.UUID,
    field_def_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> None:
    """Delete a FieldDef record.

    On success, returns HTTP 204 No Content.  A deletion event is
    published asynchronously via the message broker after the
    transaction commits.
    """
    service.delete_field_def(
        db=db,
        tenant_id=tenant_id,
        field_def_id=field_def_id,
    )
    return None


__all__ = ["router"]