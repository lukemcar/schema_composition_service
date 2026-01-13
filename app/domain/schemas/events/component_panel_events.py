"""
Event payload schemas for the ComponentPanel domain.

Messages published for ComponentPanel lifecycle events.
"""

from __future__ import annotations

from typing import Dict, Any
from uuid import UUID

from pydantic import BaseModel


class ComponentPanelCreatedMessage(BaseModel):
    tenant_id: UUID
    component_panel_id: UUID
    component_id: UUID
    payload: Dict[str, Any]


class ComponentPanelUpdatedMessage(BaseModel):
    tenant_id: UUID
    component_panel_id: UUID
    component_id: UUID
    changes: Dict[str, Any]
    payload: Dict[str, Any]


class ComponentPanelDeletedMessage(BaseModel):
    tenant_id: UUID
    component_panel_id: UUID
    component_id: UUID