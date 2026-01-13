"""
Event payload schemas for the FormPanelField domain.

Messages for creation, update and deletion of form panel field placements.
"""

from __future__ import annotations

from typing import Dict, Any
from uuid import UUID

from pydantic import BaseModel


class FormPanelFieldCreatedMessage(BaseModel):
    tenant_id: UUID
    form_panel_field_id: UUID
    form_panel_id: UUID
    field_def_id: UUID
    payload: Dict[str, Any]


class FormPanelFieldUpdatedMessage(BaseModel):
    tenant_id: UUID
    form_panel_field_id: UUID
    form_panel_id: UUID
    field_def_id: UUID
    changes: Dict[str, Any]
    payload: Dict[str, Any]


class FormPanelFieldDeletedMessage(BaseModel):
    tenant_id: UUID
    form_panel_field_id: UUID
    form_panel_id: UUID
    field_def_id: UUID