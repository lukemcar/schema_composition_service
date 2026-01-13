"""
FastAPI routes for the FormSubmissionValue resource.

FormSubmissionValues store individual field values captured within a
submission. Each value is identified by its submission and a fully
qualified field instance path. This router provides CRUD operations
scoped to a tenant.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.util.jwt_util import auth_jwt
from app.domain.schemas import (
    FormSubmissionValueCreate,
    FormSubmissionValueUpdate,
    FormSubmissionValueOut,
    FormSubmissionValueListResponse,
)
from app.domain.services import form_submission_value_service


router = APIRouter(
    prefix="/tenants/{tenant_id}/form-submission-values",
    tags=["form-submission-values"],
)


@router.get(
    "/",
    response_model=FormSubmissionValueListResponse,
)
def list_form_submission_values(
    *,
    tenant_id: uuid.UUID,
    form_submission_id: Optional[uuid.UUID] = Query(
        default=None, description="Filter by form submission ID"
    ),
    field_instance_path: Optional[str] = Query(
        default=None, description="Filter by fully qualified field instance path"
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
) -> FormSubmissionValueListResponse:
    """Retrieve a paginated list of FormSubmissionValue records for a tenant."""
    items, total = form_submission_value_service.list_form_submission_values(
        db=db,
        tenant_id=tenant_id,
        form_submission_id=form_submission_id,
        field_instance_path=field_instance_path,
        limit=limit,
        offset=offset,
    )
    return FormSubmissionValueListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.post(
    "/",
    response_model=FormSubmissionValueOut,
    status_code=status.HTTP_201_CREATED,
)
def create_form_submission_value(
    *,
    tenant_id: uuid.UUID,
    value_in: FormSubmissionValueCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormSubmissionValueOut:
    """Create a new FormSubmissionValue for the specified tenant."""
    created_by = current_user.get("sub", "system")
    value = form_submission_value_service.create_form_submission_value(
        db=db,
        tenant_id=tenant_id,
        data=value_in,
        created_by=created_by,
    )
    return value


@router.get(
    "/{form_submission_value_id}",
    response_model=FormSubmissionValueOut,
)
def get_form_submission_value(
    *,
    tenant_id: uuid.UUID,
    form_submission_value_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormSubmissionValueOut:
    """Retrieve a single FormSubmissionValue by its identifier."""
    return form_submission_value_service.get_form_submission_value(
        db=db,
        tenant_id=tenant_id,
        form_submission_value_id=form_submission_value_id,
    )


@router.put(
    "/{form_submission_value_id}",
    response_model=FormSubmissionValueOut,
)
def update_form_submission_value(
    *,
    tenant_id: uuid.UUID,
    form_submission_value_id: uuid.UUID,
    value_in: FormSubmissionValueUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormSubmissionValueOut:
    """Replace a FormSubmissionValue record with the provided fields."""
    modified_by = current_user.get("sub", "system")
    value = form_submission_value_service.update_form_submission_value(
        db=db,
        tenant_id=tenant_id,
        form_submission_value_id=form_submission_value_id,
        data=value_in,
        modified_by=modified_by,
    )
    return value


@router.delete(
    "/{form_submission_value_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_form_submission_value(
    *,
    tenant_id: uuid.UUID,
    form_submission_value_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> None:
    """Delete a FormSubmissionValue record."""
    form_submission_value_service.delete_form_submission_value(
        db=db,
        tenant_id=tenant_id,
        form_submission_value_id=form_submission_value_id,
    )
    return None


__all__ = ["router"]