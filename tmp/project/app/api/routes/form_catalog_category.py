"""
FastAPI routes for the FormCatalogCategory resource.

This module defines a REST API for creating, retrieving, listing,
updating and deleting FormCatalogCategory instances.  All
operations are tenant‑scoped: the tenant identifier must be provided
as a path parameter and the JWT token presented by the caller must
include a matching ``tenant_id`` claim.  When adding a new domain
object copy this file and adjust the router prefix, schemas and
service calls accordingly.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.util.jwt_util import auth_jwt
from app.domain.schemas import (
    FormCatalogCategoryCreate,
    FormCatalogCategoryUpdate,
    FormCatalogCategoryOut,
    FormCatalogCategoryListResponse,
)
from app.domain.services import form_catalog_category_service as category_service


# ---------------------------------------------------------------------------
# Router configuration
#
# The prefix embeds the tenant identifier in the URL path.  All routes in
# this router operate on resources owned by a single tenant.  The
# ``tags`` argument groups the endpoints in the generated OpenAPI
# documentation.
router = APIRouter(
    prefix="/tenants/{tenant_id}/form-catalog-categories",
    tags=["form-catalog-categories"],
)


@router.get(
    "/",
    response_model=FormCatalogCategoryListResponse,
)
def list_form_catalog_categories(
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
) -> FormCatalogCategoryListResponse:
    """Retrieve a paginated list of FormCatalogCategory records for a tenant.

    This endpoint returns a paginated collection of FormCatalogCategory objects.
    The caller must supply a valid JWT token with a ``tenant_id`` claim
    matching the path parameter.  Optional ``limit`` and ``offset``
    query parameters control pagination.
    """
    items, total = category_service.list_form_catalog_categories(
        db=db,
        tenant_id=tenant_id,
        limit=limit,
        offset=offset,
    )
    return FormCatalogCategoryListResponse(items=items, total=total, limit=limit, offset=offset)


@router.post(
    "/",
    response_model=FormCatalogCategoryOut,
    status_code=status.HTTP_201_CREATED,
)
def create_form_catalog_category(
    *,
    tenant_id: uuid.UUID,
    category_in: FormCatalogCategoryCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormCatalogCategoryOut:
    """Create a new FormCatalogCategory for the specified tenant.

    The ``tenant_id`` is derived from the path and validated against the
    JWT via the ``auth_jwt`` dependency.  The ``created_by`` user is
    inferred from the JWT ``sub`` claim if present, falling back to
    "system" otherwise.
    """
    created_by = current_user.get("sub", "system")
    category = category_service.create_form_catalog_category(
        db=db,
        tenant_id=tenant_id,
        data=category_in,
        created_by=created_by,
    )
    return category


@router.get(
    "/{form_catalog_category_id}",
    response_model=FormCatalogCategoryOut,
)
def get_form_catalog_category(
    *,
    tenant_id: uuid.UUID,
    form_catalog_category_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormCatalogCategoryOut:
    """Retrieve a single FormCatalogCategory by its identifier for the given tenant."""
    return category_service.get_form_catalog_category(
        db=db,
        tenant_id=tenant_id,
        form_catalog_category_id=form_catalog_category_id,
    )


@router.put(
    "/{form_catalog_category_id}",
    response_model=FormCatalogCategoryOut,
)
def update_form_catalog_category(
    *,
    tenant_id: uuid.UUID,
    form_catalog_category_id: uuid.UUID,
    category_in: FormCatalogCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> FormCatalogCategoryOut:
    """
    Replace a FormCatalogCategory record with the provided fields.

    Only fields provided in the request body are updated.  The
    ``modified_by`` user is taken from the JWT ``sub`` claim if
    available.
    """
    modified_by = current_user.get("sub", "system")
    category = category_service.update_form_catalog_category(
        db=db,
        tenant_id=tenant_id,
        form_catalog_category_id=form_catalog_category_id,
        data=category_in,
        modified_by=modified_by,
    )
    return category


@router.delete(
    "/{form_catalog_category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_form_catalog_category(
    *,
    tenant_id: uuid.UUID,
    form_catalog_category_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_jwt({"tenant_id": "{tenant_id}"})),
) -> None:
    """Delete a FormCatalogCategory record.

    On success, returns HTTP 204 No Content.  A deletion event is
    published asynchronously via the message broker after the
    transaction commits.
    """
    category_service.delete_form_catalog_category(
        db=db,
        tenant_id=tenant_id,
        form_catalog_category_id=form_catalog_category_id,
    )
    return None


__all__ = ["router"]