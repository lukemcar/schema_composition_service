"""
FastAPI routes for the FormPanelField resource.

FormPanelFields represent field instances placed directly onto a
FormPanel. They allow form designers to include ad hoc fields that are
not part of a reusable component. This router provides CRUD
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
    FormPanelFieldCreate,
    FormPanelFieldUpdate,
    FormPanelFieldOut,
    FormPanelFieldListResponse,
)
from app.domain.services import form_panel_field_service


router = APIRouter(
    prefix="/tenants/{tenant_id}/form-panel-fields",
    tags=["form-panel-fields"],
)


@router.get(
    "/",
    response_model=FormPanelFieldListResponse,
)
def list_form_panel_fields(
    *,
    tenant_id: uuid.UUID,
    form_panel_id: Optional[uuid.UUID] = Query(
        default=None, description="Filter by parent form panel ID"
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
) -> FormPanelFieldListResponse:
    """Retrieve a paginated list of FormPanelField records for a tenant."""
    items, total = form_panel_field_service.list_form_panel_fields(
        db=db,
        tenant_id=tenant_id,
        form_panel_id=form_panel_id,
        field_def_id=field_def_id,
        limit=limit,
        offset=offset,
    )
    return FormPanelFieldListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/",
    response_model=FormPanelFieldOut,
    status_code=status.HTTP_201_CREATED,
)
def create_form_panel_field(
    *,
    tenant_id: uuid.UUID,
    panel_field_in: FormPanelFieldCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormPanelFieldOut:
    """Create a new FormPanelField for the specified tenant."""
    created_by = current_user.get("sub", "system")
    panel_field = form_panel_field_service.create_form_panel_field(
        db=db,
        tenant_id=tenant_id,
        data=panel_field_in,
        created_by=created_by,
    )
    return panel_field


@router.get(
    "/{form_panel_field_id}",
    response_model=FormPanelFieldOut,
)
def get_form_panel_field(
    *,
    tenant_id: uuid.UUID,
    form_panel_field_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormPanelFieldOut:
    """Retrieve a single FormPanelField by its identifier."""
    return form_panel_field_service.get_form_panel_field(
        db=db,
        tenant_id=tenant_id,
        form_panel_field_id=form_panel_field_id,
    )


@router.put(
    "/{form_panel_field_id}",
    response_model=FormPanelFieldOut,
)
def update_form_panel_field(
    *,
    tenant_id: uuid.UUID,
    form_panel_field_id: uuid.UUID,
    panel_field_in: FormPanelFieldUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormPanelFieldOut:
    """Replace a FormPanelField record with the provided fields."""
    modified_by = current_user.get("sub", "system")
    panel_field = form_panel_field_service.update_form_panel_field(
        db=db,
        tenant_id=tenant_id,
        form_panel_field_id=form_panel_field_id,
        data=panel_field_in,
        modified_by=modified_by,
    )
    return panel_field


@router.delete(
    "/{form_panel_field_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_form_panel_field(
    *,
    tenant_id: uuid.UUID,
    form_panel_field_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> None:
    """Delete a FormPanelField record."""
    form_panel_field_service.delete_form_panel_field(
        db=db,
        tenant_id=tenant_id,
        form_panel_field_id=form_panel_field_id,
    )
    return None


__all__ = ["router"]