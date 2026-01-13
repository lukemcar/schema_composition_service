"""
FastAPI routes for the FieldDefOption resource.

This module defines REST endpoints for creating, retrieving, listing,
updating and deleting FieldDefOption instances. FieldDefOptions define
the allowed choices for single‑select and multi‑select fields and are
scoped to a tenant and field definition.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.util.jwt_util import auth_jwt
from app.domain.schemas import (
    FieldDefOptionCreate,
    FieldDefOptionUpdate,
    FieldDefOptionOut,
    FieldDefOptionListResponse,
)
from app.domain.services import field_def_option_service as option_service


router = APIRouter(
    prefix="/tenants/{tenant_id}/field-def-options",
    tags=["field-def-options"],
)


@router.get(
    "/",
    response_model=FieldDefOptionListResponse,
)
def list_field_def_options(
    *,
    tenant_id: uuid.UUID,
    field_def_id: Optional[uuid.UUID] = Query(
        default=None, description="Filter by parent field definition ID"
    ),
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
) -> FieldDefOptionListResponse:
    """Retrieve a paginated list of FieldDefOption records for a tenant."""
    items, total = option_service.list_field_def_options(
        db=db,
        tenant_id=tenant_id,
        field_def_id=field_def_id,
        limit=limit,
        offset=offset,
    )
    return FieldDefOptionListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/",
    response_model=FieldDefOptionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_field_def_option(
    *,
    tenant_id: uuid.UUID,
    option_in: FieldDefOptionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FieldDefOptionOut:
    """Create a new FieldDefOption for the specified tenant and field definition."""
    created_by = current_user.get("sub", "system")
    option = option_service.create_field_def_option(
        db=db,
        tenant_id=tenant_id,
        data=option_in,
        created_by=created_by,
    )
    return option


@router.get(
    "/{field_def_option_id}",
    response_model=FieldDefOptionOut,
)
def get_field_def_option(
    *,
    tenant_id: uuid.UUID,
    field_def_option_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FieldDefOptionOut:
    """Retrieve a single FieldDefOption by its identifier."""
    return option_service.get_field_def_option(
        db=db,
        tenant_id=tenant_id,
        field_def_option_id=field_def_option_id,
    )


@router.put(
    "/{field_def_option_id}",
    response_model=FieldDefOptionOut,
)
def update_field_def_option(
    *,
    tenant_id: uuid.UUID,
    field_def_option_id: uuid.UUID,
    option_in: FieldDefOptionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FieldDefOptionOut:
    """Replace a FieldDefOption record with the provided fields."""
    modified_by = current_user.get("sub", "system")
    option = option_service.update_field_def_option(
        db=db,
        tenant_id=tenant_id,
        field_def_option_id=field_def_option_id,
        data=option_in,
        modified_by=modified_by,
    )
    return option


@router.delete(
    "/{field_def_option_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_field_def_option(
    *,
    tenant_id: uuid.UUID,
    field_def_option_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> None:
    """Delete a FieldDefOption record."""
    option_service.delete_field_def_option(
        db=db,
        tenant_id=tenant_id,
        field_def_option_id=field_def_option_id,
    )
    return None


__all__ = ["router"]