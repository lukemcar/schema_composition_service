"""
FastAPI routes for the FormSubmission resource.

FormSubmissions represent data entry instances for a Form. This
router provides endpoints to list, create, retrieve, update and
delete submission envelopes. Individual field values are managed via
the FormSubmissionValue endpoints.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.util.jwt_util import auth_jwt
from app.domain.schemas import (
    FormSubmissionCreate,
    FormSubmissionUpdate,
    FormSubmissionOut,
    FormSubmissionListResponse,
)
from app.domain.services import form_submission_service


router = APIRouter(
    prefix="/tenants/{tenant_id}/form-submissions",
    tags=["form-submissions"],
)


@router.get(
    "/",
    response_model=FormSubmissionListResponse,
)
def list_form_submissions(
    *,
    tenant_id: uuid.UUID,
    form_id: Optional[uuid.UUID] = Query(
        default=None, description="Filter by form ID"
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
) -> FormSubmissionListResponse:
    """Retrieve a paginated list of FormSubmission records for a tenant."""
    items, total = form_submission_service.list_form_submissions(
        db=db,
        tenant_id=tenant_id,
        form_id=form_id,
        limit=limit,
        offset=offset,
    )
    return FormSubmissionListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/",
    response_model=FormSubmissionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_form_submission(
    *,
    tenant_id: uuid.UUID,
    submission_in: FormSubmissionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormSubmissionOut:
    """Create a new FormSubmission for the specified tenant."""
    created_by = current_user.get("sub", "system")
    submission = form_submission_service.create_form_submission(
        db=db,
        tenant_id=tenant_id,
        data=submission_in,
        created_by=created_by,
    )
    return submission


@router.get(
    "/{form_submission_id}",
    response_model=FormSubmissionOut,
)
def get_form_submission(
    *,
    tenant_id: uuid.UUID,
    form_submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormSubmissionOut:
    """Retrieve a single FormSubmission by its identifier."""
    return form_submission_service.get_form_submission(
        db=db,
        tenant_id=tenant_id,
        form_submission_id=form_submission_id,
    )


@router.put(
    "/{form_submission_id}",
    response_model=FormSubmissionOut,
)
def update_form_submission(
    *,
    tenant_id: uuid.UUID,
    form_submission_id: uuid.UUID,
    submission_in: FormSubmissionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormSubmissionOut:
    """Replace a FormSubmission record with the provided fields."""
    modified_by = current_user.get("sub", "system")
    submission = form_submission_service.update_form_submission(
        db=db,
        tenant_id=tenant_id,
        form_submission_id=form_submission_id,
        data=submission_in,
        modified_by=modified_by,
    )
    return submission


@router.delete(
    "/{form_submission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_form_submission(
    *,
    tenant_id: uuid.UUID,
    form_submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> None:
    """Delete a FormSubmission record."""
    form_submission_service.delete_form_submission(
        db=db,
        tenant_id=tenant_id,
        form_submission_id=form_submission_id,
    )
    return None


__all__ = ["router"]