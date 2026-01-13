"""
FastAPI routes for the Form resource.

Forms represent reusable form definitions used for data capture. This
router provides endpoints to list, create, retrieve, update and delete
form records scoped to a tenant.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.util.jwt_util import auth_jwt
from app.domain.schemas import (
    FormCreate,
    FormUpdate,
    FormOut,
    FormListResponse,
)
from app.domain.services import form_service


router = APIRouter(
    prefix="/tenants/{tenant_id}/forms",
    tags=["forms"],
)


@router.get(
    "/",
    response_model=FormListResponse,
)
def list_forms(
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
) -> FormListResponse:
    """Retrieve a paginated list of Form records for a tenant."""
    items, total = form_service.list_forms(
        db=db,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )
    return FormListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/",
    response_model=FormOut,
    status_code=status.HTTP_201_CREATED,
)
def create_form(
    *,
    tenant_id: uuid.UUID,
    form_in: FormCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormOut:
    """Create a new Form for the specified tenant."""
    created_by = current_user.get("sub", "system")
    form = form_service.create_form(
        db=db,
        tenant_id=tenant_id,
        data=form_in,
        created_by=created_by,
    )
    return form


@router.get(
    "/{form_id}",
    response_model=FormOut,
)
def get_form(
    *,
    tenant_id: uuid.UUID,
    form_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormOut:
    """Retrieve a single Form by its identifier."""
    return form_service.get_form(
        db=db,
        tenant_id=tenant_id,
        form_id=form_id,
    )


@router.put(
    "/{form_id}",
    response_model=FormOut,
)
def update_form(
    *,
    tenant_id: uuid.UUID,
    form_id: uuid.UUID,
    form_in: FormUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormOut:
    """Replace a Form record with the provided fields."""
    modified_by = current_user.get("sub", "system")
    form = form_service.update_form(
        db=db,
        tenant_id=tenant_id,
        form_id=form_id,
        data=form_in,
        modified_by=modified_by,
    )
    return form


@router.delete(
    "/{form_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_form(
    *,
    tenant_id: uuid.UUID,
    form_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> None:
    """Delete a Form record."""
    form_service.delete_form(
        db=db,
        tenant_id=tenant_id,
        form_id=form_id,
    )
    return None


__all__ = ["router"]