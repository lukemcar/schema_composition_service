"""
FastAPI routes for the ComponentPanelField resource.

ComponentPanelFields link a FieldDef to a ComponentPanel, allowing
components to place field definitions onto their panels with
overrides and ordering. This router exposes CRUD operations for
these associations.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.util.jwt_util import auth_jwt
from app.domain.schemas import (
    ComponentPanelFieldCreate,
    ComponentPanelFieldUpdate,
    ComponentPanelFieldOut,
    ComponentPanelFieldListResponse,
)
from app.domain.services import component_panel_field_service


router = APIRouter(
    prefix="/tenants/{tenant_id}/component-panel-fields",
    tags=["component-panel-fields"],
)


@router.get(
    "/",
    response_model=ComponentPanelFieldListResponse,
)
def list_component_panel_fields(
    *,
    tenant_id: uuid.UUID,
    component_panel_id: Optional[uuid.UUID] = Query(
        default=None, description="Filter by parent component panel ID"
    ),
    field_def_id: Optional[uuid.UUID] = Query(
        default=None, description="Filter by field definition ID"
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
) -> ComponentPanelFieldListResponse:
    """Retrieve a paginated list of ComponentPanelField records for a tenant."""
    items, total = component_panel_field_service.list_component_panel_fields(
        db=db,
        tenant_id=tenant_id,
        component_panel_id=component_panel_id,
        field_def_id=field_def_id,
        limit=limit,
        offset=offset,
    )
    return ComponentPanelFieldListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/",
    response_model=ComponentPanelFieldOut,
    status_code=status.HTTP_201_CREATED,
)
def create_component_panel_field(
    *,
    tenant_id: uuid.UUID,
    panel_field_in: ComponentPanelFieldCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> ComponentPanelFieldOut:
    """Create a new ComponentPanelField for the specified tenant."""
    created_by = current_user.get("sub", "system")
    panel_field = component_panel_field_service.create_component_panel_field(
        db=db,
        tenant_id=tenant_id,
        data=panel_field_in,
        created_by=created_by,
    )
    return panel_field


@router.get(
    "/{component_panel_field_id}",
    response_model=ComponentPanelFieldOut,
)
def get_component_panel_field(
    *,
    tenant_id: uuid.UUID,
    component_panel_field_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> ComponentPanelFieldOut:
    """Retrieve a single ComponentPanelField by its identifier."""
    return component_panel_field_service.get_component_panel_field(
        db=db,
        tenant_id=tenant_id,
        component_panel_field_id=component_panel_field_id,
    )


@router.put(
    "/{component_panel_field_id}",
    response_model=ComponentPanelFieldOut,
)
def update_component_panel_field(
    *,
    tenant_id: uuid.UUID,
    component_panel_field_id: uuid.UUID,
    panel_field_in: ComponentPanelFieldUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> ComponentPanelFieldOut:
    """Replace a ComponentPanelField record with the provided fields."""
    modified_by = current_user.get("sub", "system")
    panel_field = component_panel_field_service.update_component_panel_field(
        db=db,
        tenant_id=tenant_id,
        component_panel_field_id=component_panel_field_id,
        data=panel_field_in,
        modified_by=modified_by,
    )
    return panel_field


@router.delete(
    "/{component_panel_field_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_component_panel_field(
    *,
    tenant_id: uuid.UUID,
    component_panel_field_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> None:
    """Delete a ComponentPanelField record."""
    component_panel_field_service.delete_component_panel_field(
        db=db,
        tenant_id=tenant_id,
        component_panel_field_id=component_panel_field_id,
    )
    return None


__all__ = ["router"]