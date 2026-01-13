"""
FastAPI routes for the FormPanelComponent resource.

FormPanelComponents represent the placement of a reusable Component
within a FormPanel, with optional configuration overrides. This
router provides CRUD operations scoped to a tenant.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.util.jwt_util import auth_jwt
from app.domain.schemas import (
    FormPanelComponentCreate,
    FormPanelComponentUpdate,
    FormPanelComponentOut,
    FormPanelComponentListResponse,
)
from app.domain.services import form_panel_component_service


router = APIRouter(
    prefix="/tenants/{tenant_id}/form-panel-components",
    tags=["form-panel-components"],
)


@router.get(
    "/",
    response_model=FormPanelComponentListResponse,
)
def list_form_panel_components(
    *,
    tenant_id: uuid.UUID,
    form_panel_id: Optional[uuid.UUID] = Query(
        default=None, description="Filter by parent form panel ID"
    ),
    component_id: Optional[uuid.UUID] = Query(
        default=None, description="Filter by component ID"
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
) -> FormPanelComponentListResponse:
    """Retrieve a paginated list of FormPanelComponent records for a tenant."""
    items, total = form_panel_component_service.list_form_panel_components(
        db=db,
        tenant_id=tenant_id,
        form_panel_id=form_panel_id,
        component_id=component_id,
        limit=limit,
        offset=offset,
    )
    return FormPanelComponentListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.post(
    "/",
    response_model=FormPanelComponentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_form_panel_component(
    *,
    tenant_id: uuid.UUID,
    panel_component_in: FormPanelComponentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormPanelComponentOut:
    """Create a new FormPanelComponent for the specified tenant."""
    created_by = current_user.get("sub", "system")
    panel_component = form_panel_component_service.create_form_panel_component(
        db=db,
        tenant_id=tenant_id,
        data=panel_component_in,
        created_by=created_by,
    )
    return panel_component


@router.get(
    "/{form_panel_component_id}",
    response_model=FormPanelComponentOut,
)
def get_form_panel_component(
    *,
    tenant_id: uuid.UUID,
    form_panel_component_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormPanelComponentOut:
    """Retrieve a single FormPanelComponent by its identifier."""
    return form_panel_component_service.get_form_panel_component(
        db=db,
        tenant_id=tenant_id,
        form_panel_component_id=form_panel_component_id,
    )


@router.put(
    "/{form_panel_component_id}",
    response_model=FormPanelComponentOut,
)
def update_form_panel_component(
    *,
    tenant_id: uuid.UUID,
    form_panel_component_id: uuid.UUID,
    panel_component_in: FormPanelComponentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormPanelComponentOut:
    """Replace a FormPanelComponent record with the provided fields."""
    modified_by = current_user.get("sub", "system")
    panel_component = form_panel_component_service.update_form_panel_component(
        db=db,
        tenant_id=tenant_id,
        form_panel_component_id=form_panel_component_id,
        data=panel_component_in,
        modified_by=modified_by,
    )
    return panel_component


@router.delete(
    "/{form_panel_component_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_form_panel_component(
    *,
    tenant_id: uuid.UUID,
    form_panel_component_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> None:
    """Delete a FormPanelComponent record."""
    form_panel_component_service.delete_form_panel_component(
        db=db,
        tenant_id=tenant_id,
        form_panel_component_id=form_panel_component_id,
    )
    return None


__all__ = ["router"]