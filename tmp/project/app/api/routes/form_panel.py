"""
FastAPI routes for the FormPanel resource.

FormPanels define nested panels within a Form. They can optionally
reference parent panels to support hierarchical layouts. This router
provides CRUD operations scoped to a tenant.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.util.jwt_util import auth_jwt
from app.domain.schemas import (
    FormPanelCreate,
    FormPanelUpdate,
    FormPanelOut,
    FormPanelListResponse,
)
from app.domain.services import form_panel_service


router = APIRouter(
    prefix="/tenants/{tenant_id}/form-panels",
    tags=["form-panels"],
)


@router.get(
    "/",
    response_model=FormPanelListResponse,
)
def list_form_panels(
    *,
    tenant_id: uuid.UUID,
    form_id: Optional[uuid.UUID] = Query(
        default=None, description="Filter by parent form ID"
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
) -> FormPanelListResponse:
    """Retrieve a paginated list of FormPanel records for a tenant."""
    items, total = form_panel_service.list_form_panels(
        db=db,
        tenant_id=tenant_id,
        form_id=form_id,
        limit=limit,
        offset=offset,
    )
    # Note: parent_panel_id filter is currently unused in the service but
    # included here for extensibility.
    return FormPanelListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/",
    response_model=FormPanelOut,
    status_code=status.HTTP_201_CREATED,
)
def create_form_panel(
    *,
    tenant_id: uuid.UUID,
    panel_in: FormPanelCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormPanelOut:
    """Create a new FormPanel for the specified tenant."""
    created_by = current_user.get("sub", "system")
    panel = form_panel_service.create_form_panel(
        db=db,
        tenant_id=tenant_id,
        data=panel_in,
        created_by=created_by,
    )
    return panel


@router.get(
    "/{form_panel_id}",
    response_model=FormPanelOut,
)
def get_form_panel(
    *,
    tenant_id: uuid.UUID,
    form_panel_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormPanelOut:
    """Retrieve a single FormPanel by its identifier."""
    return form_panel_service.get_form_panel(
        db=db,
        tenant_id=tenant_id,
        form_panel_id=form_panel_id,
    )


@router.put(
    "/{form_panel_id}",
    response_model=FormPanelOut,
)
def update_form_panel(
    *,
    tenant_id: uuid.UUID,
    form_panel_id: uuid.UUID,
    panel_in: FormPanelUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormPanelOut:
    """Replace a FormPanel record with the provided fields."""
    modified_by = current_user.get("sub", "system")
    panel = form_panel_service.update_form_panel(
        db=db,
        tenant_id=tenant_id,
        form_panel_id=form_panel_id,
        data=panel_in,
        modified_by=modified_by,
    )
    return panel


@router.delete(
    "/{form_panel_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_form_panel(
    *,
    tenant_id: uuid.UUID,
    form_panel_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> None:
    """Delete a FormPanel record."""
    form_panel_service.delete_form_panel(
        db=db,
        tenant_id=tenant_id,
        form_panel_id=form_panel_id,
    )
    return None


__all__ = ["router"]