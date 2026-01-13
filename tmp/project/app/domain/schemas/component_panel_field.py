"""
Pydantic schemas for the ComponentPanelField domain.

These schemas define the shape of data for creating, updating, and returning
fields placed on a ComponentPanel.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.schemas.common import PaginationEnvelope


class ComponentPanelFieldBase(BaseModel):
    """Shared fields for ComponentPanelField create/update."""

    component_panel_id: UUID
    field_def_id: UUID
    overrides: Optional[Dict[str, Any]] = None
    field_order: Optional[int] = 0
    is_required: Optional[bool] = False
    created_by: Optional[str] = None


class ComponentPanelFieldCreate(ComponentPanelFieldBase):
    """Schema for creating a ComponentPanelField."""

    pass


class ComponentPanelFieldUpdate(BaseModel):
    """Schema for updating a ComponentPanelField."""

    component_panel_id: Optional[UUID] = None
    field_def_id: Optional[UUID] = None
    overrides: Optional[Dict[str, Any]] = None
    field_order: Optional[int] = None
    is_required: Optional[bool] = None
    updated_by: Optional[str] = None


class ComponentPanelFieldOut(ComponentPanelFieldBase):
    """Schema for returning a ComponentPanelField."""

    component_panel_field_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComponentPanelFieldListResponse(PaginationEnvelope[ComponentPanelFieldOut]):
    """Paginated response for ComponentPanelFields."""

    items: List[ComponentPanelFieldOut]