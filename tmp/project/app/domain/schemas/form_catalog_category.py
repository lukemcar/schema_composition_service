"""
Pydantic schemas for the FormCatalogCategory API.

These models define the shape of data accepted and returned by the
FormCatalogCategory endpoints.  Use ``FormCatalogCategoryCreate``
for creating new instances, ``FormCatalogCategoryUpdate`` for
partial updates and ``FormCatalogCategoryOut`` for responses.  A
paginated list response is provided via ``FormCatalogCategoryListResponse``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.common import PaginationEnvelope


class FormCatalogCategoryBase(BaseModel):
    """Shared attributes for creation and update operations."""

    category_key: str = Field(
        ..., description="Stable identifier used for import/export and marketplace alignment"
    )
    category_name: str = Field(
        ..., description="Human‑readable label shown in builder UI"
    )
    description: Optional[str] = Field(
        default=None, description="Optional description for admin/builder UI"
    )
    is_active: Optional[bool] = Field(
        default=True, description="Whether the category is available for selection/use"
    )
    created_by: Optional[str] = Field(
        default=None, description="Identifier of the user who created the record"
    )
    updated_by: Optional[str] = Field(
        default=None, description="Identifier of the user who last updated the record"
    )


class FormCatalogCategoryCreate(FormCatalogCategoryBase):
    """Payload for creating a new FormCatalogCategory.

    The tenant identifier is provided via the path in the API route.
    """

    pass


class FormCatalogCategoryUpdate(BaseModel):
    """Partial update model for FormCatalogCategory.

    All fields are optional to allow partial updates.  Only provided
    fields will be updated on the model.
    """

    category_key: Optional[str] = Field(
        default=None,
        description="Updated stable identifier (must remain unique within tenant)",
    )
    category_name: Optional[str] = Field(
        default=None,
        description="Updated human‑readable label",
    )
    description: Optional[str] = Field(
        default=None,
        description="Updated description",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Updated active flag",
    )
    updated_by: Optional[str] = Field(
        default=None, description="Identifier of the user performing the update"
    )


class FormCatalogCategoryOut(FormCatalogCategoryBase):
    """Response model for a FormCatalogCategory instance.

    The ``model_config.from_attributes`` option tells Pydantic to
    read values directly from the SQLAlchemy model instance when
    returning responses from the service layer.  This avoids the
    need to manually convert models to dicts.
    """

    model_config = ConfigDict(from_attributes=True)

    form_catalog_category_id: UUID = Field(
        ..., description="Primary key of the category"
    )
    tenant_id: UUID = Field(
        ..., description="Tenant that owns the category"
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the record was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the record was last updated"
    )


class FormCatalogCategoryListResponse(PaginationEnvelope[FormCatalogCategoryOut]):
    """Paginated response body for a list of FormCatalogCategory instances.

    Inherits from ``PaginationEnvelope`` to include standard pagination
    metadata such as ``total``, ``limit`` and ``offset``.  The ``items``
    field contains a list of ``FormCatalogCategoryOut`` objects.
    """

    pass


__all__ = [
    "FormCatalogCategoryCreate",
    "FormCatalogCategoryUpdate",
    "FormCatalogCategoryOut",
    "FormCatalogCategoryListResponse",
]