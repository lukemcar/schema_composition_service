"""
Pydantic schemas for the Form domain.

Forms define top‑level data collection structures. These schemas capture
basic create/update fields and the response representation.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.schemas.common import PaginationEnvelope


class FormBase(BaseModel):
    """Shared fields for Form create/update."""

    form_key: str = Field(..., max_length=200)
    version: str = Field(..., max_length=50)
    form_name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    category_id: Optional[UUID] = None
    ui_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = True
    is_published: Optional[bool] = False
    created_by: Optional[str] = None


class FormCreate(FormBase):
    """Schema for creating a Form."""

    pass


class FormUpdate(BaseModel):
    """Schema for updating a Form."""

    form_key: Optional[str] = Field(None, max_length=200)
    version: Optional[str] = Field(None, max_length=50)
    form_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    category_id: Optional[UUID] = None
    ui_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    is_published: Optional[bool] = None
    updated_by: Optional[str] = None


class FormOut(FormBase):
    """Schema for returning a Form."""

    form_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FormListResponse(PaginationEnvelope[FormOut]):
    """Paginated response for Forms."""

    items: List[FormOut]