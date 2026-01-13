"""
Event payloads for FieldDef domain events.

These message classes define the structure of the payloads sent and
received over the message bus for FieldDef lifecycle events.
Consumers of these events should depend on these models when
validating incoming messages.  Each message embeds the identifiers
required to uniquely identify the field definition and, for updates, a
``changes`` dictionary describing which fields were modified.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class FieldDefBaseMessage(BaseModel):
    tenant_id: UUID
    field_def_id: UUID


class FieldDefCreatedMessage(FieldDefBaseMessage):
    payload: Dict[str, Any]


class FieldDefUpdatedMessage(FieldDefBaseMessage):
    changes: Dict[str, Any]
    payload: Dict[str, Any]


class FieldDefDeletedMessage(FieldDefBaseMessage):
    deleted_dt: Optional[str] = None


__all__ = [
    "FieldDefCreatedMessage",
    "FieldDefUpdatedMessage",
    "FieldDefDeletedMessage",
]