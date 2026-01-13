"""
Event payload schemas for the FormPanelComponent domain.

Messages for embedding Components into FormPanels.
"""

from __future__ import annotations

from typing import Dict, Any
from uuid import UUID

from pydantic import BaseModel


class FormPanelComponentCreatedMessage(BaseModel):
    tenant_id: UUID
    form_panel_component_id: UUID
    form_panel_id: UUID
    component_id: UUID
    payload: Dict[str, Any]


class FormPanelComponentUpdatedMessage(BaseModel):
    tenant_id: UUID
    form_panel_component_id: UUID
    form_panel_id: UUID
    component_id: UUID
    changes: Dict[str, Any]
    payload: Dict[str, Any]


class FormPanelComponentDeletedMessage(BaseModel):
    tenant_id: UUID
    form_panel_component_id: UUID
    form_panel_id: UUID
    component_id: UUID