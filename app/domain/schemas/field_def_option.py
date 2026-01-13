"""
Pydantic schemas for the FieldDefOption domain.

These schemas define the shape of data used for creating, updating and
returning options associated with a FieldDef.  The list response wrapper
provides pagination metadata.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.schemas.common import PaginationEnvelope


class FieldDefOptionBase(BaseModel):
    """Shared fields for FieldDefOption.

    ``option_key`` and ``option_label`` are required on creation.  ``option_order``
    defaults to 0.  ``created_by`` can be provided to record the actor.
    """

    option_key: str = Field(..., max_length=200)
    option_label: str = Field(..., max_length=400)
    option_order: int = 0
    created_by: Optional[str] = None


class FieldDefOptionCreate(FieldDefOptionBase):
    """Schema for creating a new FieldDefOption."""

    pass


class FieldDefOptionUpdate(BaseModel):
    """Schema for updating a FieldDefOption."""

    option_key: Optional[str] = Field(None, max_length=200)
    option_label: Optional[str] = Field(None, max_length=400)
    option_order: Optional[int] = None
    updated_by: Optional[str] = None


class FieldDefOptionOut(FieldDefOptionBase):
    """Schema for returning a FieldDefOption."""

    field_def_option_id: UUID
    tenant_id: UUID
    field_def_id: UUID
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class FieldDefOptionListResponse(PaginationEnvelope[FieldDefOptionOut]):
    """Paginated response for a list of FieldDefOption objects."""

    items: List[FieldDefOptionOut]