"""
Event payload schemas for the ComponentPanelField domain.

These messages are sent when a field placement on a component panel is created,
updated or deleted.
"""

from __future__ import annotations

from typing import Dict, Any
from uuid import UUID

from pydantic import BaseModel


class ComponentPanelFieldCreatedMessage(BaseModel):
    tenant_id: UUID
    component_panel_field_id: UUID
    component_panel_id: UUID
    field_def_id: UUID
    payload: Dict[str, Any]


class ComponentPanelFieldUpdatedMessage(BaseModel):
    tenant_id: UUID
    component_panel_field_id: UUID
    component_panel_id: UUID
    field_def_id: UUID
    changes: Dict[str, Any]
    payload: Dict[str, Any]


class ComponentPanelFieldDeletedMessage(BaseModel):
    tenant_id: UUID
    component_panel_field_id: UUID
    component_panel_id: UUID
    field_def_id: UUID