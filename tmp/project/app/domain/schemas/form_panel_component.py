"""
Pydantic schemas for the FormPanelComponent domain.

These schemas define requests and responses for embedding Components into a
FormPanel.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.schemas.common import PaginationEnvelope


class FormPanelComponentBase(BaseModel):
    """Shared fields for FormPanelComponent create/update."""

    form_panel_id: UUID
    component_id: UUID
    config: Optional[Dict[str, Any]] = None
    component_order: Optional[int] = 0
    created_by: Optional[str] = None


class FormPanelComponentCreate(FormPanelComponentBase):
    """Schema for creating a FormPanelComponent."""

    pass


class FormPanelComponentUpdate(BaseModel):
    """Schema for updating a FormPanelComponent."""

    form_panel_id: Optional[UUID] = None
    component_id: Optional[UUID] = None
    config: Optional[Dict[str, Any]] = None
    component_order: Optional[int] = None
    updated_by: Optional[str] = None


class FormPanelComponentOut(FormPanelComponentBase):
    """Schema for returning a FormPanelComponent."""

    form_panel_component_id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FormPanelComponentListResponse(PaginationEnvelope[FormPanelComponentOut]):
    """Paginated response for FormPanelComponents."""

    items: List[FormPanelComponentOut]