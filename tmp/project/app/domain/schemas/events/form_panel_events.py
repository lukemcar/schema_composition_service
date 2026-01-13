"""
Event payload schemas for the FormPanel domain.

Messages for creation, update and deletion of form panels.
"""

from __future__ import annotations

from typing import Dict, Any
from uuid import UUID

from pydantic import BaseModel


class FormPanelCreatedMessage(BaseModel):
    tenant_id: UUID
    form_panel_id: UUID
    form_id: UUID
    payload: Dict[str, Any]


class FormPanelUpdatedMessage(BaseModel):
    tenant_id: UUID
    form_panel_id: UUID
    form_id: UUID
    changes: Dict[str, Any]
    payload: Dict[str, Any]


class FormPanelDeletedMessage(BaseModel):
    tenant_id: UUID
    form_panel_id: UUID
    form_id: UUID