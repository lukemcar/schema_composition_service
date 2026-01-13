"""
Event payload schemas for the FieldDefOption domain.

These classes define the shape of the payloads published when a
FieldDefOption is created, updated or deleted.  They are used by the
messaging layer to serialise messages.
"""

from __future__ import annotations

from typing import Dict, Any
from uuid import UUID

from pydantic import BaseModel


class FieldDefOptionCreatedMessage(BaseModel):
    tenant_id: UUID
    field_def_option_id: UUID
    field_def_id: UUID
    payload: Dict[str, Any]


class FieldDefOptionUpdatedMessage(BaseModel):
    tenant_id: UUID
    field_def_option_id: UUID
    field_def_id: UUID
    changes: Dict[str, Any]
    payload: Dict[str, Any]


class FieldDefOptionDeletedMessage(BaseModel):
    tenant_id: UUID
    field_def_option_id: UUID
    field_def_id: UUID