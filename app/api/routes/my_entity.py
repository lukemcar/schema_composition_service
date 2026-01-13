"""
FastAPI routes for the MyEntity resource.

This module defines a minimal REST API for creating, retrieving,
listing, updating and deleting MyEntity instances.  All operations are
strictly tenant‑scoped: the tenant identifier must be provided as a
path parameter and the JWT token presented by the caller must
include a matching ``tenant_id`` claim.  When adding a new domain
object copy this file and adjust the router prefix, schemas and
service calls accordingly.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.util.jwt_util import auth_jwt
from app.domain.schemas import (
    MyEntityCreate,
    MyEntityUpdate,
    MyEntityOut,
    MyEntityListResponse,
)

from app.domain.schemas.json_patch import JsonPatchRequest

from app.domain.services import my_entity_service as entity_service


# ---------------------------------------------------------------------------
# Router configuration
#
# The prefix embeds the tenant identifier in the URL path.  All routes in
# this router operate on resources owned by a single tenant.  The
# ``tags`` argument groups the endpoints in the generated OpenAPI
# documentation.
router = APIRouter(
    prefix="/tenants/{tenant_id}/my-entities",
    tags=["my-entities"],
)


@router.get(
    "/",
    response_model=MyEntityListResponse,
)
def list_my_entities(
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
) -> MyEntityListResponse:
    """Retrieve a paginated list of MyEntity records for a tenant.

    This endpoint returns a paginated collection of MyEntity objects.
    The caller must supply a valid JWT token with a ``tenant_id`` claim
    matching the path parameter.  Optional ``limit`` and ``offset``
    query parameters control pagination.
    """
    items, total = entity_service.list_my_entities(
        db=db,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )
    return MyEntityListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/",
    response_model=MyEntityOut,
    status_code=status.HTTP_201_CREATED,
)
def create_my_entity(
    *,
    tenant_id: uuid.UUID,
    my_entity_in: MyEntityCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> MyEntityOut:
    """Create a new MyEntity for the specified tenant.

    The ``tenant_id`` is derived from the path and validated against the
    JWT via the ``auth_jwt`` dependency.  The ``created_by`` user is
    inferred from the JWT ``sub`` claim if present, falling back to
    "system" otherwise.
    """
    created_by = current_user.get("sub", "system")
    entity = entity_service.create_my_entity(
        db=db,
        tenant_id=tenant_id,
        data=my_entity_in,
        created_by=created_by,
    )
    return entity


@router.get(
    "/{my_entity_id}",
    response_model=MyEntityOut,
)
def get_my_entity(
    *,
    tenant_id: uuid.UUID,
    my_entity_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> MyEntityOut:
    """Retrieve a single MyEntity by its identifier for the given tenant."""
    return entity_service.get_my_entity(
        db=db,
        tenant_id=tenant_id,
        my_entity_id=my_entity_id,
    )


@router.put(
    "/{my_entity_id}",
    response_model=MyEntityOut,
)
def update_my_entity(
    *,
    tenant_id: uuid.UUID,
    my_entity_id: uuid.UUID,
    my_entity_in: MyEntityUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> MyEntityOut:
    """
    Replace a MyEntity record with the provided fields.

    Only fields provided in the request body are updated.  The
    ``modified_by`` user is taken from the JWT ``sub`` claim if
    available.
    """
    modified_by = current_user.get("sub", "system")
    entity = entity_service.update_my_entity(
        db=db,
        tenant_id=tenant_id,
        my_entity_id=my_entity_id,
        data=my_entity_in,
        modified_by=modified_by,
    )
    return entity


@router.delete(
    "/{my_entity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_my_entity(
    *,
    tenant_id: uuid.UUID,
    my_entity_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> None:
    """Delete a MyEntity record.

    On success, returns HTTP 204 No Content.  A deletion event is
    published asynchronously via the message broker after the
    transaction commits.
    """
    entity_service.delete_my_entity(
        db=db,
        tenant_id=tenant_id,
        my_entity_id=my_entity_id,
    )
    return None


@router.patch(
    "/{my_entity_id}",
    response_model=MyEntityOut,
)
def patch_my_entity(
    *,
    tenant_id: uuid.UUID,
    my_entity_id: uuid.UUID,
    patch_request: JsonPatchRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> MyEntityOut:
    """
    Apply a JSON Patch (RFC‑6902) request to a MyEntity record.

    Supported paths:
      - /name
      - /data
      - /data/<nested…> (JSON Pointer into the data dict/list)

    Supported operations: add, replace, remove.
    """
    modified_by = current_user.get("sub", "system")
    entity = entity_service.patch_my_entity(
        db=db,
        tenant_id=tenant_id,
        my_entity_id=my_entity_id,
        patch_request=patch_request,
        modified_by=modified_by,
    )
    return entity
