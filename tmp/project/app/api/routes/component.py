"""
FastAPI routes for the Component resource.

Components represent reusable UI elements that can be embedded into
forms or other components. This router exposes CRUD operations for
components scoped to a tenant.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.util.jwt_util import auth_jwt
from app.domain.schemas import (
    ComponentCreate,
    ComponentUpdate,
    ComponentOut,
    ComponentListResponse,
)
from app.domain.services import component_service


router = APIRouter(
    prefix="/tenants/{tenant_id}/components",
    tags=["components"],
)


@router.get(
    "/",
    response_model=ComponentListResponse,
)
def list_components(
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
) -> ComponentListResponse:
    """Retrieve a paginated list of Component records for a tenant."""
    items, total = component_service.list_components(
        db=db,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )
    return ComponentListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/",
    response_model=ComponentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_component(
    *,
    tenant_id: uuid.UUID,
    component_in: ComponentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> ComponentOut:
    """Create a new Component for the specified tenant."""
    created_by = current_user.get("sub", "system")
    component = component_service.create_component(
        db=db,
        tenant_id=tenant_id,
        data=component_in,
        created_by=created_by,
    )
    return component


@router.get(
    "/{component_id}",
    response_model=ComponentOut,
)
def get_component(
    *,
    tenant_id: uuid.UUID,
    component_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> ComponentOut:
    """Retrieve a single Component by its identifier."""
    return component_service.get_component(
        db=db,
        tenant_id=tenant_id,
        component_id=component_id,
    )


@router.put(
    "/{component_id}",
    response_model=ComponentOut,
)
def update_component(
    *,
    tenant_id: uuid.UUID,
    component_id: uuid.UUID,
    component_in: ComponentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> ComponentOut:
    """Replace a Component record with the provided fields."""
    modified_by = current_user.get("sub", "system")
    component = component_service.update_component(
        db=db,
        tenant_id=tenant_id,
        component_id=component_id,
        data=component_in,
        modified_by=modified_by,
    )
    return component


@router.delete(
    "/{component_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_component(
    *,
    tenant_id: uuid.UUID,
    component_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> None:
    """Delete a Component record."""
    component_service.delete_component(
        db=db,
        tenant_id=tenant_id,
        component_id=component_id,
    )
    return None


__all__ = ["router"]