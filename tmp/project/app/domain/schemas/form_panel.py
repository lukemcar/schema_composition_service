"""
Pydantic schemas for the FormPanel domain.

Panels group elements within a Form and can nest other panels. These
schemas capture create/update fields and response representation.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.schemas.common import PaginationEnvelope


class FormPanelBase(BaseModel):
    """Shared fields for FormPanel create/update."""

    form_id: UUID
    parent_panel_id: Optional[UUID] = None
    panel_key: str = Field(..., max_length=200)
    panel_label: Optional[str] = Field(None, max_length=100)
    ui_config: Optional[Dict[str, Any]] = None
    panel_order: Optional[int] = 0
    created_by: Optional[str] = None


class FormPanelCreate(FormPanelBase):
    """Schema for creating a FormPanel."""

    pass


class FormPanelUpdate(BaseModel):
    """Schema for updating a FormPanel."""

    form_id: Optional[UUID] = None
    parent_panel_id: Optional[UUID] = None
    panel_key: Optional[str] = Field(None, max_length=200)
    panel_label: Optional[str] = Field(None, max_length=100)
    ui_config: Optional[Dict[str, Any]] = None
    panel_order: Optional[int] = None
    updated_by: Optional[str] = None


class FormPanelOut(FormPanelBase):
    """Schema for returning a FormPanel."""

    form_panel_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FormPanelListResponse(PaginationEnvelope[FormPanelOut]):
    """Paginated response for FormPanels."""

    items: List[FormPanelOut]