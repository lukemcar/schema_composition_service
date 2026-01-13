"""
FastAPI routes for the ComponentPanel resource.

ComponentPanels define nested panels within a Component, allowing for
grouping and ordering of UI elements. This router exposes CRUD
operations scoped to a tenant.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.util.jwt_util import auth_jwt
from app.domain.schemas import (
    ComponentPanelCreate,
    ComponentPanelUpdate,
    ComponentPanelOut,
    ComponentPanelListResponse,
)
from app.domain.services import component_panel_service


router = APIRouter(
    prefix="/tenants/{tenant_id}/component-panels",
    tags=["component-panels"],
)


@router.get(
    "/",
    response_model=ComponentPanelListResponse,
)
def list_component_panels(
    *,
    tenant_id: uuid.UUID,
    component_id: Optional[uuid.UUID] = Query(
        default=None, description="Filter by parent component ID"
    ),
    parent_panel_id: Optional[uuid.UUID] = Query(
        default=None, description="Filter by parent panel ID"
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
) -> ComponentPanelListResponse:
    """Retrieve a paginated list of ComponentPanel records for a tenant."""
    items, total = component_panel_service.list_component_panels(
        db=db,
        tenant_id=tenant_id,
        component_id=component_id,
        parent_panel_id=parent_panel_id,
        limit=limit,
        offset=offset,
    )
    return ComponentPanelListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/",
    response_model=ComponentPanelOut,
    status_code=status.HTTP_201_CREATED,
)
def create_component_panel(
    *,
    tenant_id: uuid.UUID,
    panel_in: ComponentPanelCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> ComponentPanelOut:
    """Create a new ComponentPanel for the specified tenant."""
    created_by = current_user.get("sub", "system")
    panel = component_panel_service.create_component_panel(
        db=db,
        tenant_id=tenant_id,
        data=panel_in,
        created_by=created_by,
    )
    return panel


@router.get(
    "/{component_panel_id}",
    response_model=ComponentPanelOut,
)
def get_component_panel(
    *,
    tenant_id: uuid.UUID,
    component_panel_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> ComponentPanelOut:
    """Retrieve a single ComponentPanel by its identifier."""
    return component_panel_service.get_component_panel(
        db=db,
        tenant_id=tenant_id,
        component_panel_id=component_panel_id,
    )


@router.put(
    "/{component_panel_id}",
    response_model=ComponentPanelOut,
)
def update_component_panel(
    *,
    tenant_id: uuid.UUID,
    component_panel_id: uuid.UUID,
    panel_in: ComponentPanelUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> ComponentPanelOut:
    """Replace a ComponentPanel record with the provided fields."""
    modified_by = current_user.get("sub", "system")
    panel = component_panel_service.update_component_panel(
        db=db,
        tenant_id=tenant_id,
        component_panel_id=component_panel_id,
        data=panel_in,
        modified_by=modified_by,
    )
    return panel


@router.delete(
    "/{component_panel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_component_panel(
    *,
    tenant_id: uuid.UUID,
    component_panel_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> None:
    """Delete a ComponentPanel record."""
    component_panel_service.delete_component_panel(
        db=db,
        tenant_id=tenant_id,
        component_panel_id=component_panel_id,
    )
    return None


__all__ = ["router"]