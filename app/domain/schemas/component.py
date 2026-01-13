"""
Pydantic schemas for the Component domain.

These schemas define the shape of data used for creating, updating and
returning reusable UI components. Components are identified by a stable
business key and version scoped to a tenant.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.schemas.common import PaginationEnvelope


class ComponentBase(BaseModel):
    """Shared fields for Component create/update."""

    component_key: str = Field(..., max_length=200)
    version: str = Field(..., max_length=50)
    component_name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    category_id: Optional[UUID] = None
    ui_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = True
    created_by: Optional[str] = None


class ComponentCreate(ComponentBase):
    """Schema for creating a Component."""

    pass


class ComponentUpdate(BaseModel):
    """Schema for updating a Component."""

    component_key: Optional[str] = Field(None, max_length=200)
    version: Optional[str] = Field(None, max_length=50)
    component_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    category_id: Optional[UUID] = None
    ui_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    updated_by: Optional[str] = None


class ComponentOut(ComponentBase):
    """Schema for returning a Component."""

    component_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComponentListResponse(PaginationEnvelope[ComponentOut]):
    """Paginated response for Components."""

    items: List[ComponentOut]