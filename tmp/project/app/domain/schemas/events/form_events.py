"""
Event payload schemas for the Form domain.

Messages for Form lifecycle events (created, updated, deleted).
"""

from __future__ import annotations

from typing import Dict, Any
from uuid import UUID

from pydantic import BaseModel


class FormCreatedMessage(BaseModel):
    tenant_id: UUID
    form_id: UUID
    payload: Dict[str, Any]


class FormUpdatedMessage(BaseModel):
    tenant_id: UUID
    form_id: UUID
    changes: Dict[str, Any]
    payload: Dict[str, Any]


class FormDeletedMessage(BaseModel):
    tenant_id: UUID
    form_id: UUID