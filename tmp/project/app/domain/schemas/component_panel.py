"""
Pydantic schemas for the ComponentPanel domain.

These schemas describe requests and responses for ComponentPanel
operations. Panels organize fields and nested panels within a component.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.schemas.common import PaginationEnvelope


class ComponentPanelBase(BaseModel):
    """Shared fields for ComponentPanel create/update."""

    component_id: UUID
    parent_panel_id: Optional[UUID] = None
    panel_key: str = Field(..., max_length=200)
    panel_label: Optional[str] = Field(None, max_length=100)
    ui_config: Optional[Dict[str, Any]] = None
    panel_order: Optional[int] = 0
    created_by: Optional[str] = None


class ComponentPanelCreate(ComponentPanelBase):
    """Schema for creating a ComponentPanel."""

    pass


class ComponentPanelUpdate(BaseModel):
    """Schema for updating a ComponentPanel."""

    component_id: Optional[UUID] = None
    parent_panel_id: Optional[UUID] = None
    panel_key: Optional[str] = Field(None, max_length=200)
    panel_label: Optional[str] = Field(None, max_length=100)
    ui_config: Optional[Dict[str, Any]] = None
    panel_order: Optional[int] = None
    updated_by: Optional[str] = None


class ComponentPanelOut(ComponentPanelBase):
    """Schema for returning a ComponentPanel."""

    component_panel_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ComponentPanelListResponse(PaginationEnvelope[ComponentPanelOut]):
    """Paginated response for ComponentPanels."""

    items: List[ComponentPanelOut]