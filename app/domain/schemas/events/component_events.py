"""
Event payload schemas for the Component domain.

These messages are published when a Component is created, updated or deleted.
The payload contains the serialized Component model after creation or update.
"""

from __future__ import annotations

from typing import Dict, Any
from uuid import UUID

from pydantic import BaseModel


class ComponentCreatedMessage(BaseModel):
    tenant_id: UUID
    component_id: UUID
    payload: Dict[str, Any]


class ComponentUpdatedMessage(BaseModel):
    tenant_id: UUID
    component_id: UUID
    changes: Dict[str, Any]
    payload: Dict[str, Any]


class ComponentDeletedMessage(BaseModel):
    tenant_id: UUID
    component_id: UUID